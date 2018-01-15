from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
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
    url(r'^experimentstool/', include('experimentstool.urls')),
    url(r'^visualization/', include('remotedesktops.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^', include('sso.urls')),
]
