import xml.etree.ElementTree as ET
from flattentool.sort_iati import sort_iati_element, IATISchemaWalker


def child_to_xml(parent_el, tagname, child):
    if hasattr(child, 'items'):
        parent_el.append(dict_to_xml(child, tagname))
    else:
        if tagname.startswith('@'):
            parent_el.attrib[tagname[1:]] = str(child)
        elif tagname == 'text()':
            parent_el.text = str(child)
        else:
            raise('Everything should end with text() or an attirbute!')


def dict_to_xml(data, tagname):
    el = ET.Element(tagname)
    for k, v in data.items():
        if type(v) == list:
            for item in v:
                child_to_xml(el, k, item)
        else:
            child_to_xml(el, k, v)
    return el


def toxml(data, xml_schemas=None):
    root = dict_to_xml(data, 'iati-activities')
    if xml_schemas is not None:
        schema_dict = IATISchemaWalker(xml_schemas).create_schema_dict('iati-activity')
        for element in root:
            sort_iati_element(element, schema_dict)
    return ET.tostring(root)
