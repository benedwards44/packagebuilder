from buildpackage.models import Package, ComponentType, Component
from suds.client import Client
from lxml import etree

def get_components(instance_url, api_version, org_id, access_token):
	# instantiate the metadata WSDL
	metadata_client = Client('http://packagebuilder.herokuapp.com/static/metadata.wsdl.xml')

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

	# If a component type has no child components, remove the component type altogether
	for component_type in ComponentType.objects.filter(package=package.id):
		if not Component.objects.filter(component_type=component_type.id):
			component_type.delete()

	return str(package.id)