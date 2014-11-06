from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from buildpackage.forms import LoginForm, ComponentSelectForm
from buildpackage.models import Package, ComponentType, Component
from django.contrib import messages
from django.forms.models import modelformset_factory
from django.conf import settings
from buildpackage.tasks import query_components_from_org
from suds.client import Client
from lxml import etree
from time import sleep
import json
from packagexml import build_xml
import requests

def index(request):
	
	if request.method == 'POST':

		login_form = LoginForm(request.POST)

		if login_form.is_valid():

			environment = login_form.cleaned_data['environment']
			api_version = login_form.cleaned_data['api_version']

			oauth_url = 'https://login.salesforce.com/services/oauth2/authorize'
			if environment == 'Sandbox':
				oauth_url = 'https://test.salesforce.com/services/oauth2/authorize'

			oauth_url = oauth_url + '?response_type=code&client_id=' + settings.SALESFORCE_CONSUMER_KEY + '&redirect_uri=' + settings.SALESFORCE_REDIRECT_URI + '&state='+ environment + str(api_version)
			
			return HttpResponseRedirect(oauth_url)
	else:
		login_form = LoginForm()

	return render_to_response('index.html', RequestContext(request,{'login_form': login_form}))

def oauth_response(request):

	error_exists = False
	error_message = ''
	username = ''
	org_name = ''

	if request.GET:

		oauth_code = request.GET.get('code')
		environment = request.GET.get('state')[:-2]
		api_version = request.GET.get('state')[-2:]
		access_token = ''
		instance_url = ''
		org_id = ''

		if 'Production' in environment:
			login_url = 'https://login.salesforce.com'
		else:
			login_url = 'https://test.salesforce.com'
		
		r = requests.post(login_url + '/services/oauth2/token', headers={ 'content-type':'application/x-www-form-urlencoded'}, data={'grant_type':'authorization_code','client_id': settings.SALESFORCE_CONSUMER_KEY,'client_secret':settings.SALESFORCE_CONSUMER_SECRET,'redirect_uri': settings.SALESFORCE_REDIRECT_URI,'code': oauth_code})
		auth_response = json.loads(r.text)

		if 'error_description' in auth_response:
			error_exists = True
			error_message = auth_response['error_description']
		else:
			access_token = auth_response['access_token']
			instance_url = auth_response['instance_url']
			user_id = auth_response['id'][-18:]
			org_id = auth_response['id'][:-19]
			org_id = org_id[-18:]

			# get username of the authenticated user
			r = requests.get(instance_url + '/services/data/v' + api_version + '.0/sobjects/User/' + user_id + '?fields=Username', headers={'Authorization': 'OAuth ' + access_token})
			query_response = json.loads(r.text)
			username = query_response['Username']

			# get the org name of the authenticated user
			r = requests.get(instance_url + '/services/data/v' + api_version + '.0/sobjects/Organization/' + org_id + '?fields=Name', headers={'Authorization': 'OAuth ' + access_token})
			org_name = json.loads(r.text)['Name']

		login_form = LoginForm(initial={'environment': environment, 'api_version': api_version, 'access_token': access_token, 'instance_url': instance_url, 'org_id': org_id})	

	if request.POST:

		login_form = LoginForm(request.POST)

		if login_form.is_valid():

			environment = login_form.cleaned_data['environment']
			api_version = login_form.cleaned_data['api_version']
			access_token = login_form.cleaned_data['access_token']
			instance_url = login_form.cleaned_data['instance_url']
			org_id = login_form.cleaned_data['org_id']

			if 'logout' in request.POST:
				r = requests.post(instance_url + '/services/oauth2/revoke', headers={'content-type':'application/x-www-form-urlencoded'}, data={'token': access_token})
				instance = instance_url.replace('https://','').replace('.salesforce.com','')
				return HttpResponseRedirect('/logout?instance=' + instance)

			if 'get_components' in request.POST:

				# create the package record to store results
				package = Package()
				package.username = org_id
				package.api_version = str(api_version) + '.0'
				package.status = 'Running'
				package.save()

				# Queue job to run async
				try:
					query_components_from_org.delay(package, instance_url, api_version, org_id, access_token)
				except:
					# If fail above, wait 5 seconds and try again. Not ideal but should work for now
					sleep(5)
					try:
						query_components_from_org.delay(package, instance_url, api_version, org_id, access_token)
					except:
						# Sleep another 5
						sleep(5)
						query_components_from_org.delay(package, instance_url, api_version, org_id, access_token)

				return HttpResponseRedirect('/loading/' + str(package.id))

	return render_to_response('oauth_response.html', RequestContext(request,{'error': error_exists, 'error_message': error_message, 'username': username, 'org_name': org_name, 'login_form': login_form}))

# AJAX endpoint for page to constantly check if job is finished
def job_status(request, package_id):
	package = get_object_or_404(Package, pk=package_id)
	return HttpResponse(package.status + ':::' + package.error)

# Page for user to wait for job to run
def loading(request, package_id):

	package = get_object_or_404(Package, pk=package_id)

	# If finished already (unlikely) direct to schema view
	if package.status == 'Finished':
		return HttpResponseRedirect('/package/' + str(package.id))
	else:
		return render_to_response('loading.html', RequestContext(request, {'package': package}))	

# Skipping this step for now
def select_components(request, package_id):

	package = get_object_or_404(Package, pk=package_id)

	# query for component types and components seperately. Need to do this for the field sets
	component_types = ComponentType.objects.filter(package=package_id).order_by('name')
	components = Component.objects.filter(component_type__package=package_id)

	# build field sets for the page
	ComponentTypeFormSet = modelformset_factory(ComponentType, extra=0, fields=('id','include_all','name'))
	ComponentFormSet = modelformset_factory(Component, extra=0, fields=('component_type','include','name'))

	if request.method == 'POST':

		# three different forms for the page
		component_select_form = ComponentSelectForm(request.POST)
		component_type_formset = ComponentTypeFormSet(request.POST, queryset=component_types, prefix='component_type')
		component_formset = ComponentFormSet(request.POST, queryset=components, prefix='component')

		if component_select_form.is_valid():

			# only need to save the fieldsets if the user has played with the partial options
			if component_select_form.cleaned_data['component_option'] == 'partial':
				component_type_formset.save()
				component_formset.save()

			package.package = build_xml(package)
			package.save()

			return HttpResponseRedirect('/package/' + str(package.id))

	else:
		component_select_form = ComponentSelectForm()
		component_type_formset = ComponentTypeFormSet(queryset=component_types, prefix='component_type')
		component_formset = ComponentFormSet(queryset=components, prefix='component')

	return render_to_response('select_components.html', RequestContext(request, {'package': package, 'component_select_form': component_select_form,'component_type_formset': component_type_formset,'component_formset': component_formset}))

def package(request, package_id):
	package = get_object_or_404(Package, pk=package_id)
	package_xml = build_xml(package)
	package.delete()
	return render_to_response('package.html', RequestContext(request, {'package_xml': package_xml}))

def logout(request):
	instance = request.GET.get('instance')
	return render_to_response('logout.html', RequestContext(request, {'instance': instance}))