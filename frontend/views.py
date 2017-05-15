from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from django import forms
from frontend.models import UserProfile, OrganisationProfile
from frontend.forms import (PrettyForm, extendToPrettyForm, UserForm,
                            UserProfileForm, OrganisationProfileForm,
                            SearchBarForm)
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
#from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q
from datetime import datetime

import ldap
import ldap.modlist as modlist

import sha
from base64 import b64encode

from registration.backends.simple.views import RegistrationView

class FrontendRegistration(RegistrationView):

    def register(self, form):
        print "are we there yet?"
        newuser = super(FrontendRegistration, self).register(form)

        user_profile = UserProfile(user=newuser)
        user_profile.save() 

        create_user_in_ldap(newuser.username, 
                            form.cleaned_data['password1'],
                            user_profile.uidnumber)

        print "are we?"
        return newuser

    def get_success_url(self, user):
        #return '/frontend/'
        return '/'

def index(request):
    return render(request,'frontend/index.html')

def create_user_in_ldap(username, password, uidnumber):

    # Open a connection
    l = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)

    # Bind/authenticate with a user with apropriate rights to add objects
    l.simple_bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # The dn of our new entry/object
    dn="cn="+ username +",dc=ldap,dc=portal,dc=com"
    #dn="cn=python_test,ou=People,dc=coegss,dc=hlrs,dc=de" 

    ctx = sha.new(password) 
    hash = "{SHA}" + b64encode(ctx.digest())

    # A dict to help build the "body" of the object
    attrs = {}
    attrs['uid'] = [str(username)]
    attrs['uidNumber'] = [str(uidnumber+500)]
    attrs['gidNumber'] = ['100']
    attrs['objectclass'] = ['inetOrgPerson','organizationalPerson','person','posixAccount','top']
    attrs['cn'] = str(username)
    attrs['sn'] = str(username)
    attrs['userPassword'] = hash
    #attrs['description'] = 'test_python_user'
    attrs['homeDirectory'] = '/home/users/' + str(username)

    # Convert our dict to nice syntax for the add-function using modlist-module
    ldif = modlist.addModlist(attrs)

    # Do the actual synchronous add-operation to the ldapserver
    l.add_s(dn,ldif)

    # Disconnect and free resources when done
    l.unbind_s()


@login_required
def restricted(request):
    return render(request, 'frontend/restricted.html', {})
    
@login_required
def user_logout(request):
    logout(request)

    return HttpResponseRedirect('/frontend/')

def about(request):
    return render(request, 'frontend/about.html', {})

@login_required
def profile(request):
    if request.method == 'POST':
        form1 = UserForm(request.POST, instance=request.user)
        #form2 = UserProfileForm(request.user.is_superuser, request.POST, instance=request.user.userprofile)
        # For now we allow everyone to choose their organisation and claim ownership
        form2 = UserProfileForm(True, request.POST, instance=request.user.userprofile)
        if (form1.is_valid() and form2.is_valid()):
            form1.save()
            form2.save()
    else:
        form1 = UserForm(instance=request.user)
        #form2 = UserProfileForm(request.user.is_superuser, instance=request.user.userprofile)
        form2 = UserProfileForm(True, instance=request.user.userprofile)
    org = request.user.userprofile.organisation
    extendToPrettyForm(form1)
    extendToPrettyForm(form2)
    return render(request, 'frontend/profile.html', { 'user': request.user, 'org': org, 'form1': form1, 'form2': form2 })

def create_pager(search_query, current, total):
    url = reverse('yellow_pages')
    class PagerNumber:
        number  = True
        dir     = False
        current = False
        def __init__(self, clickable, num):
            self.clickable = clickable
            self.label = '{}'.format(num)
            self.href = '{}?{}p={}'.format(url, search_query, num)
    class PagerDir:
        number  = False
        dir     = True
        current = False
        def __init__(self, clickable, num, label):
            self.clickable = clickable
            self.label = label
            self.href = '{}?{}p={}'.format(url, search_query, num)
    class Current:
        number    = False
        dir       = False
        current   = True
        clickable = False
        def __init__(self, num):
            self.label = '{}'.format(num)
    class Dots:
        number    = False
        dir       = False
        current   = False
        clickable = False
        label     = '...'

    # These constants should be moved to configuration.
    # We could also use Paginator here.
    results_per_page = 2
    adjacent         = 2
    pages = (total + results_per_page - 1) / results_per_page

    if current > pages:
        raise Http404("Not found")

    lower_bound = max(1, current - adjacent)
    upper_bound = min(pages, current + adjacent)
    results_lower_bound = (current-1) * results_per_page
    results_upper_bound = current * results_per_page

    # Skip the pager if we have a single page
    if pages == 1:
        return ((results_lower_bound, results_upper_bound), None)

    return ((results_lower_bound, results_upper_bound),
               [ PagerDir(1 < current, n, 'prev') for n in [current-1]]
             + [ PagerNumber(True, n) for n in [1] if 1 < lower_bound ]
             + [ Dots() for n in [1] if 2 < lower_bound ]
             + [ PagerNumber(True, n) for n in range(lower_bound, current) ]
             + [ Current(current) ]
             + [ PagerNumber(True, n) for n in range(current + 1, upper_bound + 1) ]
             + [ Dots() for n in [1] if upper_bound < pages - 1 ]
             + [ PagerNumber(True, n) for n in [pages] if upper_bound < pages ]
             + [ PagerDir(current < pages, n, 'next') for n in [current+1]])

@login_required
@csrf_exempt
def yellow_pages(request):
    form = SearchBarForm(request.GET or None)
    if(form.is_valid() and ('search' in form.cleaned_data)):
        raw_terms = form.cleaned_data['search'].split() # Split the search string on whitespace
        topics = []
        search_terms = []
        for tx in raw_terms:
            t = tx.split(':') # Check if we have a 'topic:x' term
            if (len(t) == 2 and t[0].lower() == 'topic'):
                topics.append(t[1].lower())
            else:
                search_terms.extend(t)

        orgs = OrganisationProfile.objects.all()
        for t in topics:
            orgs = orgs.filter(topics__name=t)
        for s in search_terms:
            orgs = orgs.filter(Q(name__icontains=s) | Q(description__icontains=s))
    else:
        orgs = OrganisationProfile.objects.all()

    # To assemble the URLs for the pager links, we need to take into account
    # the search query.
    search_query = form.is_valid() \
                   and ('search' in form.cleaned_data) \
                   and 'search={}&'.format(form.cleaned_data['search']) or ''

    total = orgs.count()
    current = form.is_valid() and form.cleaned_data['p'] or 1

    ((lb, ub), pager) = create_pager(search_query, current, total)

    orgs_subset = orgs[lb:ub]

    return render(request, 'frontend/yellowpages.html',
                  { 'orgs': orgs_subset, 'form': form, 'total' : total,
                    'pager_template': 'frontend/search_pager.html', 'pager': pager })

@login_required
def organisation_profile(request, pid):
    profile = OrganisationProfile.objects.get(id=pid)
    return render(request, 'frontend/org_profile.html', { 'profile': profile })

@login_required
def organisation_profile_edit(request, oid_raw):
    oid = int(oid_raw)
    if (not request.user.is_superuser and
           (request.user.userprofile.organisation.id != oid or not request.user.userprofile.is_owner)):
        raise PermissionDenied
    profile = OrganisationProfile.objects.get(id=oid)
    if request.method == 'POST':
        form = OrganisationProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('organisation_profile', oid)
    else:
        form = OrganisationProfileForm(instance=profile)
    extendToPrettyForm(form)
    return render(request, 'frontend/org_profile_edit.html', { 'profile': profile, 'form': form })

@login_required
def organisation_profile_new(request):
    #if not request.user.is_superuser:
    #    raise PermissionDenied
    if request.method == 'POST':
        form = OrganisationProfileForm (request.POST)
        if form.is_valid():
            profile = form.save()
            print profile
            return redirect('organisation_profile', profile.id)
    else:
        form = OrganisationProfileForm()
    extendToPrettyForm(form)
    return render(request, 'frontend/org_profile_edit.html', { 'form': form })


def ckan(request):
    return render(request, 'frontend/ckan.html', {})

def moodle(request):
    return render(request, 'frontend/moodle.html', {})

def askbot(request):
    return render(request, 'frontend/askbot.html', {})

