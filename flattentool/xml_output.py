try:
    import lxml.etree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from warnings import warn
from flattentool.exceptions import DataErrorWarning


def child_to_xml(parent_el, tagname, child):
    if hasattr(child, 'items'):
        child_el = dict_to_xml(child, tagname)
        if child_el is not None:
            parent_el.append(child_el)
    else:
        if tagname.startswith('@'):
            try:
                parent_el.attrib[tagname[1:]] = str(child)
            except ValueError as e:
                warn(str(e), DataErrorWarning)
        elif tagname == 'text()':
            parent_el.text = str(child)
        else:
            raise('Everything should end with text() or an attirbute!')


def dict_to_xml(data, tagname):
    try:
        el = ET.Element(tagname)
    except ValueError as e:
        warn(str(e), DataErrorWarning)
        return

    for k, v in data.items():
        if type(v) == list:
            for item in v:
                child_to_xml(el, k, item)
        else:
            child_to_xml(el, k, v)
    return el


def toxml(data):
    return ET.tostring(dict_to_xml(data, 'iati-activities'))
