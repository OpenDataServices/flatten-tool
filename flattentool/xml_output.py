import xml.etree.ElementTree as ET


def child_to_xml(parent_el, tagname, child):
    if hasattr(child, 'items'):
        parent_el.append(dict_to_xml(child, tagname))
    else:
        if tagname.startswith('@'):
            parent_el.attrib[tagname[1:]] = child
        elif tagname == 'text()':
            parent_el.text = child
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


def toxml(data):
    return ET.tostring(dict_to_xml(data, 'iati-activities'))
