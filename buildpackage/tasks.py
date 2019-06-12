from __future__ import absolute_import
from celery import Celery
from django.conf import settings
import os
import datetime
import traceback
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'packagebuilder.settings')

app = Celery('tasks', broker=os.environ.get('REDISTOGO_URL', 'redis://localhost'))

from buildpackage.models import Package, ComponentType, Component
from suds.client import Client
from lxml import etree

@app.task
def query_components_from_org(package):
	"""
		Query all metadata from the org and build components and component types
	"""

	try:

		package.status = 'Running'
		package.save()

		# Stored package variables - used for queries and processing
		instance_url = package.instance_url
		api_version = package.api_version
		org_id = package.username
		access_token = package.access_token

		# instantiate the metadata WSDL
		metadata_client = Client('http://packagebuilder.herokuapp.com/static/metadata-' + str(settings.SALESFORCE_API_VERSION) + '.wsdl.xml')

		# URL for metadata API
		metadata_url = instance_url + '/services/Soap/m/' + str(api_version) + '/' + org_id

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

			# If it has child names, let's use that
			if 'childXmlNames' in component_type:

				for child_component in component_type.childXmlNames:

					# create the component type record
					component_type_record = ComponentType()
					component_type_record.package = package
					component_type_record.name = child_component
					component_type_record.include_all = True
					component_type_record.save()

			# create the component type record
			component_type_record = ComponentType()
			component_type_record.package = package
			component_type_record.name = component_type.xmlName
			component_type_record.include_all = True
			component_type_record.save()

			# Component is a folder component - eg Dashboard, Document, EmailTemplate, Report
			if not component_type.inFolder:

				# If it has child names, let's use that
				if 'childXmlNames' in component_type:

					# Child component list for querying
					child_component_list = []

					# Child loop counter
					child_loop_counter = 0

					# Iterate over the child components
					for child_component in component_type.childXmlNames:

						# set up the component type to query for components
						component = metadata_client.factory.create("ListMetadataQuery")
						component.type = child_component
						if component.type == 'ManagedTopic':
							#ManagedTopic is not a valid component Type and it should be 'ManagedTopics'
							component.type = 'ManagedTopics'

						# Add metadata to list
						child_component_list.append(component)

						# Run the metadata query only if the list has reached 3 (the max allowed to query)
						# at one time, or if there is less than 3 components left to query 
						if len(child_component_list) == 3 or (len(component_type.childXmlNames) - child_loop_counter) <= 3:

							# loop through the components returned from the component query
							for component in metadata_client.service.listMetadata(child_component_list,api_version):

								# Query database for parent component_type
								component_type_query = ComponentType.objects.filter(name=component.type, package=package.id)

								# Only add if found
								if component_type_query:

									# If the user wants all components, or they don't want any packages  and it's not
									if include_component(package.component_option, component):

										# create the component record and save
										component_record = Component()
										component_record.component_type = component_type_query[0]
										component_record.name = component.fullName
										component_record.include = True
										component_record.save()

							# Clear the list
							child_component_list = []		

						# Increment count
						child_loop_counter = child_loop_counter + 1

				# set up the component type to query for components
				component = metadata_client.factory.create("ListMetadataQuery")
				component.type = component_type.xmlName

				# Add metadata to list
				component_list.append(component)

			else:

				# Append "Folder" keyword onto end of component type
				component = metadata_client.factory.create("ListMetadataQuery")

				# EmailTemplate = EmailFolder (for some reason)
				if component_type.xmlName == 'EmailTemplate':
					component.type = 'EmailFolder'
				else:
					component.type = component_type.xmlName + 'Folder'

				# Loop through folders
				for folder in metadata_client.service.listMetadata([component], api_version):

					# Create component for folder to query
					folder_component = metadata_client.factory.create("ListMetadataQuery")
					folder_component.type = component_type.xmlName
					folder_component.folder = folder.fullName

					if include_component(package.component_option, folder):

						# create the component folder entry
						component_record = Component()
						component_record.component_type = component_type_record
						component_record.name = folder.fullName
						component_record.save()

					# Loop through folder components
					for folder_component in metadata_client.service.listMetadata([folder_component], api_version):

						if include_component(package.component_option, folder_component):

							# create the component record and save
							component_record = Component()
							component_record.component_type = component_type_record
							component_record.name = folder_component.fullName
							component_record.save()


			# Run the metadata query only if the list has reached 3 (the max allowed to query)
			# at one time, or if there is less than 3 components left to query 
			if len(component_list) == 3 or (len(all_metadata[0]) - loop_counter) <= 3:

				# loop through the components returned from the component query
				for component in metadata_client.service.listMetadata(component_list,api_version):

					# Query database for parent component_type
					component_type_query = ComponentType.objects.filter(name=component.type, package=package.id)

					# Only add if found
					if component_type_query:

						# If the user wants all components, or they don't want any packages  and it's not
						if include_component(package.component_option, component):

							# create the component record and save
							component_record = Component()
							component_record.component_type = component_type_query[0]
							component_record.name = component.fullName
							component_record.include = True
							component_record.save()


						elif package.component_option == 'none' and component.namespacePrefix:

							continue


		
				# clear list once done. This list will re-build to 3 components and re-query the service
				component_list = []

			loop_counter = loop_counter + 1;

		# If a component type has no child components, remove the component type altogether
		for component_type in ComponentType.objects.filter(package=package.id):
			if not Component.objects.filter(component_type=component_type.id):
				component_type.delete()

		package.package = build_xml(package)

		package.status = 'Finished'

	except Exception as error:
		package.status = 'Error'
		package.error = traceback.format_exc()

	package.finished_date = datetime.datetime.now()
	package.save()

def build_xml(package):
	"""
		Convert component and component types into an XML
	"""

	# start our xml structure
	root = etree.Element('Package')
	root.set('xmlns','http://soap.sforce.com/2006/04/metadata')

	# start loop of components. Re-querying to take save values from above
	for component_type in ComponentType.objects.filter(package=package.id).order_by('name'):

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

	return xml_file


# Determine whether to return the component or not
def include_component(components_option, component):

	# If the user wants all components
	if components_option == 'all':
		return True

	# If the user doesn't want any package components
	elif components_option == 'none':
		# If package has a prefix, it is part of a package. Exclude it
		if 'namespacePrefix' in component:
			return False
		else:
			return True

	# If the user only wants unmanaged packages
	elif components_option == 'unmanaged':
		# If package has a prefix, it is part of a package. Exclude it
		if 'manageableState' in component:
			# If the component is unmanaged
			if component.manageableState == 'unmanaged':
				return True
			else:
				return False
		else:
			return True

	return True
