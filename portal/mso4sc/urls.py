from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='home'),
    url(r'^marketplaceLogIn/$', views.marketplace_logIn,
        name='marketplace_logIn'),
    url(r'^marketplaceLoggedIn/$', views.marketplace_loggedIn,
        name='marketplace_loggedIn'),
    url(r'^marketplace/$', views.marketplace, name='marketplace'),
    url(r'^datacatalogueLogIn/$', views.datacatalogue_logIn,
        name='datacatalogue_logIn'),
    url(r'^datacatalogueLoggedIn/$', views.datacatalogue_loggedIn,
        name='datacatalogue_loggedIn'),
    url(r'^datacatalogue/$', views.datacatalogue, name='datacatalogue'),
    url(r'^experimentstool/$', views.experimentstool, name='experimentstool'),
    url(r'^experimentstool/_get_products$',
        views.get_products, name='_get_products'),
    url(r'^experimentstool/_upload_application$',
        views.upload_blueprint, name='_upload_application'),
    url(r'^experimentstool/_get_blueprints$',
        views.get_blueprints, name='_get_blueprints'),
    url(r'^experimentstool/_get_datasets$',
        views.get_datasets, name='_get_datasets'),
    url(r'^experimentstool/_create_deployment$',
        views.create_deployment, name='_create_deployment')
]
