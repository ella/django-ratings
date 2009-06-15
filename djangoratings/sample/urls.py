from django.conf.urls.defaults import *

from djangoratings.sample import views

urlpatterns = patterns('',
    url(r'^$', views.homepage, name='djangoratings-homepage'),
)

