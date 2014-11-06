from lxml import etree
from buildpackage.models import Package, ComponentType, Component

def build_xml(package):

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