from django.urls import path
from django.views.generic import TemplateView
from django.contrib import admin
from django.conf import settings
from buildpackage import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('oauth_response/', views.oauth_response),
    path('package/<str:package_id>/', views.package),
    path('logout/', views.logout),
    path('job_status/<str:package_id>/', views.job_status),
    path('loading/<str:package_id>/', views.loading),
    path('auth_details/', views.auth_details),
    path('api/package/', views.api_create_job),
    path('api/package/status/<str:package_id>/', views.job_status),
    path('api/package/<str:package_id>/', views.get_package),
]
