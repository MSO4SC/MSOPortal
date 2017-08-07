from __future__ import unicode_literals

from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User


class Topic(models.Model):
    name = models.CharField(max_length=20, help_text='Name of the topic')

    def __unicode__(self):
        return self.name


class OrganisationProfile(models.Model):
    name        = models.CharField(max_length=50)
    description = models.TextField(max_length=1000, help_text='A few paragraphs of description', default='')
    website     = models.URLField(blank=True, max_length=100)
    email       = models.EmailField(max_length=60)
    address     = models.CharField(max_length=100)
    telephone   = models.CharField(blank=True, max_length=30)
    fax         = models.CharField(blank=True, max_length=30)

    topics      = models.ManyToManyField(Topic, blank=True)

    def __unicode__(self):
        return self.name


class Resource(models.Model):
    Category = (
        ('H', 'Hardware'),
        ('S', 'Software'),
        ('C', 'Consultancy'),
        ('D', 'Data'),
        ('O', 'Commities'),
        ('W', 'Workflow'),
        ('P', 'Project'),
    )
    name = models.CharField(max_length=30)
    category = models.CharField(max_length=1, choices=Category)

    def __str__(self):
        return self.name

    # Migration fails because of this, so commenting it out
    #class Meta:
    #    db_table = 'resource'

## It may have been tempting to add these additional fields by inheriting from the User model directly.
## However, because other applications may also want access to the User model, then it is not recommended
## to use inheritance, but instead use the one-to-one relationship.
##
class UserProfile(models.Model):
    # This line is required. Links UserProfile to a User model instance.
    user = models.OneToOneField(User)

    # The additional attributes we wish to include.
    uidnumber = models.AutoField(primary_key=True)

    organisation = models.ForeignKey(OrganisationProfile, on_delete=models.CASCADE, null=True, blank=True)
    is_owner = models.BooleanField(default=False)

    resources = models.ManyToManyField(Resource, blank=True)
    #topics = models.ManyToManyField(Topic)

    # Override the __unicode__() method to return out something meaningful!
    def __unicode__(self):
        return self.user.username

