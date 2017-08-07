from django.conf.urls import url

from . import views

app_name = 'matchmaking'
urlpatterns = [
    # ex: /matchmaking/
    url(r'^$', views.matchmaking, name='matchmaking'),
]