from django.conf.urls import url, include
from django.contrib import admin
from buildpackage import views
admin.autodiscover()



urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth_response/$', views.oauth_response),
    url(r'^package/(?P<package_id>[0-9A-Za-z_\-]+)/$', views.package),
    url(r'^logout/$', views.logout),
    url(r'^job_status/(?P<package_id>[0-9A-Za-z_\-]+)/$', views.job_status),
    url(r'^loading/(?P<package_id>[0-9A-Za-z_\-]+)/$', views.loading),
    url(r'^auth_details/$', views.auth_details),

    url(r'^api/package/$', views.api_create_job),
    url(r'^api/package/status/(?P<package_id>[0-9A-Za-z_\-]+)/$', views.job_status),
    url(r'^api/package/(?P<package_id>[-\w]+)$', views.get_package),
]
