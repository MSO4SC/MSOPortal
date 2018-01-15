from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.remotedesktops, name='remotedesktops'),
    url(r'^_get_rdi_list$',
        views.get_rdi_list, name='_get_rdi_list'),
    url(r'^_add_rdi$',
        views.add_rdi, name='_add_rdi'),
    url(r'^_delete_rdi$',
        views.delete_rdi, name='_delete_rdi'),
    url(r'^_get_rd_list$',
        views.get_rd_list, name='_get_rd_list'),
    url(r'^_add_rd$',
        views.add_rd, name='_add_rd'),
]
