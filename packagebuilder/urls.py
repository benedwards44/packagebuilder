from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'buildpackage.views.index', name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth_response/$', 'buildpackage.views.oauth_response'),
    url(r'^select_components/(?P<package_id>\d+)/$', 'buildpackage.views.select_components'),
    url(r'^package/(?P<package_id>\d+)/$', 'buildpackage.views.package'),
    url(r'^logout/$', 'buildpackage.views.logout'),
)
