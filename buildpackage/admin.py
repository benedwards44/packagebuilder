from django.contrib import admin
from buildpackage.models import Package, ComponentType, Component

class PackageAdmin(admin.ModelAdmin):
    list_display = ('username','package')

class ComponentTypeAdmin(admin.ModelAdmin):
    list_display = ('package','name')

admin.site.register(Package, PackageAdmin)
admin.site.register(ComponentType, ComponentTypeAdmin)