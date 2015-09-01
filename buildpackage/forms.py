from django import forms
from django.forms import ModelForm
from buildpackage.models import Package

class LoginForm(forms.Form):

	environment = forms.CharField(required=False);
	access_token = forms.CharField(required=False)
	instance_url = forms.CharField(required=False)
	org_id = forms.CharField(required=False)

	# Options for including packages or not
	PACKAGE_CHOICES = (
		('all','All Components'),
		('unmanaged','Exclude Managed'),
		('none','No Packaged Components'),
	)

	package_option = forms.ChoiceField(choices=PACKAGE_CHOICES, required=False)

class ComponentSelectForm(forms.Form):
	component_option = forms.CharField(required=False)

