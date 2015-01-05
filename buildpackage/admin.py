from django.contrib import admin
from buildpackage.models import Package, ComponentType, Component

class ComponentInline(admin.TabularInline):
	fields = ['name']
	ordering = ['name']
	model = ComponentType
	extra = 0

class PackageAdmin(admin.ModelAdmin):
    list_display = ('username','api_version', 'created_date','finished_date','status')
    inlines = [ComponentInline]

admin.site.register(Package, PackageAdmin)