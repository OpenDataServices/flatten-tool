import sys

from .sort_xml import XMLSchemaWalker, namespaces
from .sheet import Sheet


class XMLSchemaWalkerForTemplate(XMLSchemaWalker):
    def attribute_loop(self, element):
        """
        Returns a list containing a tuple for each attribute the given element
        can have.
        The format of the tuple is (name, is_required)
        """
        #if element.find("xsd:complexType[@mixed='true']", namespaces=namespaces) is not None:
        #    print_column_info('text', indent)
            
        a = element.attrib
        type_attributes = []
        type_attributeGroups = []
        if 'type' in a:
            complexType = self.get_schema_element('complexType', a['type'])
            if complexType is not None:
                type_attributes = (
                    complexType.findall('xsd:attribute', namespaces=namespaces) +
                    complexType.findall('xsd:simpleContent/xsd:extension/xsd:attribute', namespaces=namespaces)
                    )
                type_attributeGroups = (
                    complexType.findall('xsd:attributeGroup', namespaces=namespaces) +
                    complexType.findall('xsd:simpleContent/xsd:extension/xsd:attributeGroup', namespaces=namespaces)
                    )

        group_attributes = []
        for attributeGroup in (
                element.findall('xsd:complexType/xsd:attributeGroup', namespaces=namespaces) +
                element.findall('xsd:complexType/xsd:simpleContent/xsd:extension/xsd:attributeGroup', namespaces=namespaces) +
                type_attributeGroups
                ):
            group_attributes += self.get_schema_element('attributeGroup', attributeGroup.attrib['ref']).findall('xsd:attribute', namespaces=namespaces)

        for attribute in (
                element.findall('xsd:complexType/xsd:attribute', namespaces=namespaces) +
                element.findall('xsd:complexType/xsd:simpleContent/xsd:extension/xsd:attribute', namespaces=namespaces) +
                type_attributes + group_attributes
                ):
            doc = attribute.find(".//xsd:documentation", namespaces=namespaces)
            if 'ref' in attribute.attrib:
                referenced_attribute = self.get_schema_element('attribute', attribute.get('ref'))
                if referenced_attribute is not None:
                    attribute = referenced_attribute
                if doc is None:
                    # Only fetch the documentation of the referenced definition
                    # if we don't already have documentation.
                    doc = attribute.find(".//xsd:documentation", namespaces=namespaces)
            yield attribute.get('name') or attribute.get('ref'), attribute.get('use') == 'required'

    def has_simple_content(self, element):
        a = element.attrib
        simple_content = False
        if 'type' in a:
            complexType = self.get_schema_element('complexType', a['type'])
            if complexType is not None:
                simple_content = bool(complexType.findall('xsd:simpleContent', namespaces=namespaces))
        return simple_content or bool(element.findall('xsd:complexType/xsd:simpleContent', namespaces=namespaces))

    def generate_paths(self, parent_name, parent_element=None, parent_path=''):
        if parent_element is None:
            parent_element = self.get_schema_element('element', parent_name)

        for name, required, in self.attribute_loop(parent_element):
            if name == 'xml:lang':
                # Namespaces not supported yet https://github.com/OpenDataServices/flatten-tool/issues/148
                # And no way to specify two narrative elements anyway https://github.com/OpenDataServices/cove/issues/777
                continue
            yield parent_path + '@' + name

        for name, element, _, minOccurs, maxOccurs in self.element_loop(parent_element):
            if element is None:
                element = self.get_schema_element('element', name)
            path = parent_path + name
            if self.has_simple_content(element):
                yield path
            if maxOccurs == 'unbounded' or int(maxOccurs) > 1:
                path += '/0/'
            else:
                path += '/'
            yield from list(self.generate_paths(name, element, path))


class XMLSchemaParser(object):
    """Parse the fields of a JSON schema into a flattened structure."""

    def __init__(self, xml_schemas=[], root_list_path=None):
        self.sub_sheets = {}
        self.main_sheet = Sheet()
        self.sub_sheet_mapping = {}
        self.xml_schemas = xml_schemas
        assert root_list_path is not None
        self.root_list_path = root_list_path

    def parse(self):
        for path in XMLSchemaWalkerForTemplate(self.xml_schemas).generate_paths(self.root_list_path):
            self.main_sheet.append(path)

