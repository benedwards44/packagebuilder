from __future__ import absolute_import
from celery import Celery
from django.conf import settings
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'packagebuilder.settings')

app = Celery('tasks', broker=os.environ.get('REDISTOGO_URL', 'redis://localhost'))

from buildpackage.models import Package, ComponentType, Component
from suds.client import Client
from lxml import etree

@app.task
def query_components_from_org(package, instance_url, api_version, org_id, access_token):

	try:

		# instantiate the metadata WSDL
		metadata_client = Client('http://packagebuilder.herokuapp.com/static/metadata.wsdl.xml')

		# URL for metadata API
		metadata_url = instance_url + '/services/Soap/m/' + str(api_version) + '.0/' + org_id

		# set the metadata url based on the login result
		metadata_client.set_options(location=metadata_url)

		# set the session id from the login result
		session_header = metadata_client.factory.create("SessionHeader")
		session_header.sessionId = access_token
		metadata_client.set_options(soapheaders=session_header)
		
		# query for the list of metadata types
		all_metadata = metadata_client.service.describeMetadata(api_version)

		# Components for listing metadata
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

			# Add metadata to list
			component_list.append(component)

			# Run the metadata query only if the list has reached 3 (the max allowed to query)
			# at one time, or if there is less than 3 components left to query 
			if len(component_list) == 3 or (len(all_metadata[0]) - loop_counter) <= 3:

				# loop through the components returned from the component query
				for component in metadata_client.service.listMetadata(component_list,api_version):

					# Query database for parent component_type
					component_type_query = ComponentType.objects.filter(name=component.type, package=package.id)

					# Only add if found
					if component_type_query:

						# create the component record and save
						component_record = Component()
						component_record.component_type = component_type_query[0]
						component_record.name = component.fullName
						component_record.include = True
						component_record.save()
		
				# clear list once done. This list will re-build to 3 components and re-query the service
				component_list = []

			loop_counter = loop_counter + 1;

		# If a component type has no child components, remove the component type altogether
		for component_type in ComponentType.objects.filter(package=package.id):
			if not Component.objects.filter(component_type=component_type.id):
				component_type.delete()

		package.status = 'Finished'

	except Exception as error:
		package.status = 'Error'
		package.error = error

	package.save()

	return str(package.id)