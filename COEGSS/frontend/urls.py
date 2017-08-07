from django.conf.urls import patterns, url, include
from frontend import views
from frontend.views import FrontendRegistration

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^about/$', views.about, name='about'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^yellowpages/$', views.yellow_pages, name='yellow_pages'),
    url(r'^org_profile/(\d+)/$', views.organisation_profile, name='organisation_profile'),
    url(r'^org_profile/(\d+)/edit/$', views.organisation_profile_edit, name='organisation_profile_edit'),
    url(r'^org_profile/new/$', views.organisation_profile_new, name='organisation_profile_new'),
    url(r'^restricted/', views.restricted, name='restricted'),
    url(r'^ckan/', views.ckan, name='ckan'),
    url(r'^moodle/', views.moodle, name='moodle'),
    url(r'^askbot/', views.askbot, name='askbot'),
    url(r'^register/$', FrontendRegistration.as_view(), name='registration_register'),
    url(r'^logout/$', views.user_logout, name='registration_logout'),
    url(r'^', include('registration.backends.simple.urls')),
]

