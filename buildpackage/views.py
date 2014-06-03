from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from buildpackage.forms import LoginForm, ComponentSelectForm
from buildpackage.models import Package, ComponentType, Component
from django.contrib import messages
from django.forms.models import modelformset_factory
from django.conf import settings
import json
import requests

from suds.client import Client
from lxml import etree

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
			r = requests.get(instance_url + '/services/data/v' + api_version + '.0/sobjects/User/' + user_id + '?fields=Username', headers={'Authorization': 'OAuth ' + access_token})
			query_response = json.loads(r.text)
			username = query_response['Username']

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

				if 'Production' in environment:
					login_url = 'https://login.salesforce.com'
				else:
					login_url = 'https://test.salesforce.com'

				r = requests.post(login_url + '/services/oauth2/revoke', headers={'content-type':'application/x-www-form-urlencoded'}, data={'token': access_token})
				return HttpResponseRedirect('/logout?environment=' + environment)

			if 'get_components' in request.POST:

				# instantiate the metadata WSDL
				metadata_client = Client('/static/metadata.wsdl.xml')

				metadata_url = instance_url + '/services/Soap/m/' + str(api_version) + '.0/' + org_id

				# set the metadata url based on the login result
				metadata_client.set_options(location=metadata_url)

				# set the session id from the login result
				session_header = metadata_client.factory.create("SessionHeader")
				session_header.sessionId = access_token
				metadata_client.set_options(soapheaders=session_header)
				
				# query for the list of metadata types
				all_metadata = metadata_client.service.describeMetadata(api_version)

				# create the package record to store results
				package = Package()
				package.username = org_id
				package.api_version = str(api_version) + '.0'
				package.save()

				component_list = []

				loop_counter = 0;

				# loop through metadata types
				for component_type in all_metadata[0]:

					# create the component type record and save
					component_type_record = ComponentType()
					component_type_record.package = package
					component_type_record.name = component_type.xmlName
					component_type_record.include_all = True
					component_type_record.save()

					# set up the component type to query for components
					component = metadata_client.factory.create("ListMetadataQuery")
					component.type = component_type.xmlName
					component_list.append(component)

					if len(component_list) == 3 or (len(all_metadata[0]) - loop_counter) <= 3:

						# loop through the components returned from the component query
						for component in metadata_client.service.listMetadata(component_list,api_version):

							component_type_query = ComponentType.objects.filter(name=component.type, package=package.id)

							if component_type_query:
								# create the component record and save
								component_record = Component()
								component_record.component_type = component_type_query[0]
								component_record.name = component.fullName
								component_record.include = True
								component_record.save()
				
						component_list = []

					loop_counter = loop_counter + 1;

				for component_type in ComponentType.objects.filter(package=package.id):
					if not Component.objects.filter(component_type=component_type.id):
						component_type.delete()

				return HttpResponseRedirect('/select_components/' + str(package.id))

	return render_to_response('oauth_response.html', RequestContext(request,{'error': error_exists, 'error_message': error_message, 'username': username, 'login_form': login_form}))

def select_components(request, package_id):

	package = get_object_or_404(Package, pk=package_id)

	# query for component tpyes and components seperately. Need to do this for the field sets
	component_types = ComponentType.objects.filter(package=package_id).order_by('name')
	components = Component.objects.filter(component_type__package=package_id)

	# reset all include values back to true
	for component_type in component_types:
		component_type.include_all = True
		component_type.save()

	# reset all include values back to true
	for component in components:
		component.include = True
		component.save()

	# build field sets for the page
	ComponentTypeFormSet = modelformset_factory(ComponentType, extra=0, fields=('id','include_all','name'))
	ComponentFormSet = modelformset_factory(Component, extra=0, fields=('component_type','include','name'))

	if request.method == 'POST':

		# three different forms for the page
		component_select_form = ComponentSelectForm(request.POST)
		component_type_formset = ComponentTypeFormSet(request.POST, queryset=component_types, prefix='component_type')
		component_formset = ComponentFormSet(request.POST, queryset=components, prefix='component')

		if component_select_form.is_valid():

			# start our xml structure
			root = etree.Element('Package')
			root.set('xmlns','http://soap.sforce.com/2006/04/metadata')

			# only need to save the fieldsets if the user has played with the partial options
			if component_select_form.cleaned_data['component_option'] == 'partial':
				component_type_formset.save()
				component_formset.save()

			# start loop of components. Re-querying to take save values from above
			for component_type in ComponentType.objects.filter(package=package_id).order_by('name'):

				# create child node for each type of component
				top_child = etree.Element('types')

				# loop through components
				for component in component_type.component_set.order_by('name'):
					if component.include:
						# child XML child
						child = etree.Element('members')
						child.text = component.name
						top_child.append(child)

				# append child to xml
				child = etree.Element('name')
				child.text = component_type.name
				top_child.append(child)

				# only append if the user has selected it
				if component_type.include_all:
					root.append(top_child)

			# add the final xml node
			child = etree.Element('version')
			child.text = package.api_version
			root.append(child)

			# create file string
			xml_file = '<?xml version="1.0" encoding="UTF-8"?>\n'
			xml_file = xml_file + etree.tostring(root, pretty_print=True)

			# save xml data to the package record
			package.package = xml_file
			package.save()

			return HttpResponseRedirect('/package/' + str(package.id))

	else:
		component_select_form = ComponentSelectForm()
		component_type_formset = ComponentTypeFormSet(queryset=component_types, prefix='component_type')
		component_formset = ComponentFormSet(queryset=components, prefix='component')

	return render_to_response('select_components.html', RequestContext(request, {'package': package, 'component_select_form': component_select_form,'component_type_formset': component_type_formset,'component_formset': component_formset}))

def package(request, package_id):
	package = get_object_or_404(Package, pk=package_id)
	package_xml = package.package
	package.delete()
	return render_to_response('package.html', RequestContext(request, {'package_xml': package_xml}))

def logout(request):

	environment = request.GET.get('environment')

	if 'Production' in environment:
		logout_url = 'https://login.salesforce.com'
	else:
		logout_url = 'https://test.salesforce.com'
	return render_to_response('logout.html', RequestContext(request, {'logout_url': logout_url}))
