from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'buildpackage.views.index', name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth_response/$', 'buildpackage.views.oauth_response'),
    url(r'^select_components/(?P<package_id>\d+)/$', 'buildpackage.views.select_components'),
    url(r'^package/(?P<package_id>\d+)/$', 'buildpackage.views.package'),
    url(r'^logout/$', 'buildpackage.views.logout'),
    url(r'^waiting/$', 'buildpackage.views.waiting_job'),
    url(r'^loading/(?P<job_id>[-\w]+)/$', 'buildpackage.views.loading'),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    url(r'^django-rq/', include('django_rq.urls')),
)
