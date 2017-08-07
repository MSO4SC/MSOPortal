from django import forms
from django.contrib.auth.models import User
from frontend.models import UserProfile, OrganisationProfile #Page, Category, 
import types

'''
class CategoryForm(forms.ModelForm):
    name = forms.CharField(max_length=128, help_text="Please enter the category name.")
    views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
    likes = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
    slug = forms.CharField(widget=forms.HiddenInput(), required=False)

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = Category
        fields = ('name',)


class PageForm(forms.ModelForm):
    title = forms.CharField(max_length=128, help_text="Please enter the title of the page.")
    url = forms.URLField(max_length=200, help_text="Please enter the URL of the page.")
    views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)

    class Meta:
        # Provide an association between the ModelForm and a model
        model = Page

        # What fields do we want to include in our form?
        # This way we don't need every field in the model present.
        # Some fields may allow NULL values, so we may not want to include them...
        # Here, we are hiding the foreign key.
        # we can either exclude the category field from the form,
        exclude = ('category',)
        #or specify the fields to include (i.e. not include the category field)
        #fields = ('title', 'url', 'views')

    def clean(self):
        cleaned_data = self.cleaned_data
        url = cleaned_data.get('url')

        # If url is not empty and doesn't start with 'http://', prepend 'http://'.
        if url and not url.startswith('http://'):
            url = 'http://' + url
            cleaned_data['url'] = url

        return cleaned_data


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('picture',)
'''

def as_dl_(self):
    "Return this form rendered as HTML <dt>s and <dd>s -- excluding the <dl></dl>."
    #kwargs['label_suffix'] = ''
    return self._html_output(
        normal_row='<dt%(html_class_attr)s>%(label)s</dt><dd>%(errors)s%(field)s%(help_text)s</dd>',
        error_row='<dt><dd colspan="2">%s</dd></dt>',
        row_ender='</dd>',
        help_text_html='<span class="helptext">%s</span>',
        errors_on_separate_row=False)

def as_li2_(self):
    "Return this form rendered as HTML <li>s -- excluding the <ul></ul>. Help text is rendered inline."
    return self._html_output(
        normal_row='<li%(html_class_attr)s><label class=form-label>%(label)s</label>%(field)s%(errors)s</li>',
        error_row='%s',
        row_ender='</li>',
        help_text_html='<span class="helptext">%s</span>',
        errors_on_separate_row=False)

def add_tooltips_and_placeholders(self):
    for key in self.fields:
        self.fields[key].widget.attrs['title'] = self.fields[key].help_text
        self.fields[key].widget.attrs['placeholder'] = self.fields[key].help_text
        self.fields[key].widget.attrs['class'] = 'form-control'

class PrettyForm(forms.Form):
    "Form with tooltips and placeholders"
    def __init__ (self, *args, **kwargs):
        super(VerticalForm, self).__init__(*args, **kwargs)
        add_tooltips_and_placeholders(self)

    as_dl = as_dl_
    as_li2 = as_li2_

    def __str__(self):
        """Use as_dl() as the default rendering method. This is not working for some reason,
           so call as_dl() directly instead."""
        return self.as_dl()

def extendToPrettyForm(self):
    "We need this to 'decorate' a ModelForm."
    add_tooltips_and_placeholders(self)
    self.as_dl = types.MethodType(as_dl_, self)
    self.as_li2 = types.MethodType(as_li2_, self)


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

# We use this to create a form that shows extra fields
# for the admin. After
# http://stackoverflow.com/questions/297383/dynamically-update-modelforms-meta-class
def UserProfileForm(is_admin, *args, **kwargs):
    if is_admin:
        myfields = ['organisation', 'is_owner', 'resources']
    else:
        myfields = ['resources']
    class UserProfileFormClass(forms.ModelForm):
        class Meta:
            model = UserProfile
            fields = myfields
        def __init__(self):
            super(forms.ModelForm, self).__init__(*args, **kwargs)
    return UserProfileFormClass()

class OrganisationProfileForm(forms.ModelForm):
    class Meta:
        model = OrganisationProfile
        fields = ['name', 'description', 'website', 'email', 'address', 'telephone', 'fax', 'topics']

class SearchBarForm(forms.Form):
    search = forms.CharField(label='Search', required=False, max_length=100)
    p      = forms.IntegerField(label='Results page number', required=False, min_value=1)

