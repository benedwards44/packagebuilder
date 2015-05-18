from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'buildpackage.views.index', name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth_response/$', 'buildpackage.views.oauth_response'),
    url(r'^select_components/(?P<package_id>[0-9A-Za-z_\-]+)/$', 'buildpackage.views.select_components'),
    url(r'^package/(?P<package_id>[0-9A-Za-z_\-]+)/$', 'buildpackage.views.package'),
    url(r'^logout/$', 'buildpackage.views.logout'),
    url(r'^job_status/(?P<package_id>[0-9A-Za-z_\-]+)/$', 'buildpackage.views.job_status'),
    url(r'^loading/(?P<package_id>[0-9A-Za-z_\-]+)/$', 'buildpackage.views.loading'),
    url(r'^auth_details/$', 'buildpackage.views.auth_details'),
)
