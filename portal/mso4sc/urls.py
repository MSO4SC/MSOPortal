from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='home'),
    url(r'^marketplaceLogIn/$', views.marketplace_logIn, name='marketplace_logIn'),
    url(r'^marketplaceLoggedIn/$', views.marketplace_loggedIn,
        name='marketplace_loggedIn'),
    url(r'^marketplace/$', views.marketplace, name='marketplace')
]
