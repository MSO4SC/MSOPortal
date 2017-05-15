from __future__ import unicode_literals

from django.db import models


# The models are now in frontend. Please remove this at some point
# Create your models here.
#class Organization(models.Model):
#    name = models.CharField(max_length=100)
#    description = models.CharField(max_length=250)
#    address = models.CharField(max_length=100)
#    email = models.CharField(max_length=60)
#    telephone = models.CharField(blank=True, max_length=30)
#    fax = models.CharField(blank=True, max_length=30)
#    website = models.CharField(blank=True, max_length=100)
#
#    def __str__(self):
#        return self.name
#
#    class Meta:
#        db_table = 'organization'
#
#class Resource(models.Model):
#    Category = (
#        ('H', 'Hardware'),
#        ('S', 'Software'),
#        ('C', 'Consultancy'),
#        ('D', 'Data'),
#        ('O', 'Commities'),
#        ('W', 'Workflow'),
#        ('P', 'Project'),
#    )
#    name = models.CharField(max_length=30)
#    category = models.CharField(max_length=1, choices=Category)
#
#    def __str__(self):
#        return self.name
#
#    class Meta:
#        db_table = 'resource'
#
#class Person(models.Model):
#    first_name = models.CharField(max_length=30)
#    last_name = models.CharField(max_length=30)
#    email = models.CharField(max_length=60)
#    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True)
#    resources = models.ManyToManyField(Resource)
#
#    def __str__(self):
#        return self.first_name
#
#    class Meta:
#        db_table = 'person'
#class Category(models.Model):
#    name = models.CharField(max_length=30)#

    #class Meta:
    #    db_table = 'category'
