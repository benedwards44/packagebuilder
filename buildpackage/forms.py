from django import forms
from django.forms import ModelForm
from buildpackage.models import Package

class LoginForm(forms.Form):
	environment = forms.CharField(required=False);
	api_version = forms.IntegerField(required=False)
	access_token = forms.CharField(required=False)
	instance_url = forms.CharField(required=False)
	org_id = forms.CharField(required=False)

class ComponentSelectForm(forms.Form):
	component_option = forms.CharField(required=False)

