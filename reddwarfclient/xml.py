from lxml import etree
import json
from numbers import Number

from reddwarfclient import exceptions
from reddwarfclient.client import ReddwarfHTTPClient


XML_NS = { None: "http://docs.openstack.org/database/api/v1.0" }

# This dictionary contains XML paths of things that should become list items.
LISTIFY = {
    "accounts":[[]],
    "databases":[[]],
    "flavors": [[]],
    "instances": [[]],
    "links" : [["flavor", "instance", "instances"],
               ["instance", "instances"]],
    "hosts": [[]],
    "devices": [[]],
    "users": [[]],
    "versions": [[]],
}

REQUEST_AS_LIST = set(['databases', 'users'])

def element_ancestors_match_list(element, list):
    """
    For element root at <foo><blah><root></blah></foo> matches against
    list ["blah", "foo"].
    """
    itr_elem = element.getparent()
    for name in list:
        if itr_elem is None:
            break
        if name != normalize_tag(itr_elem):
            return False
        itr_elem = itr_elem.getparent()
    return True


def element_must_be_list(parent_element, name):
    """Determines if an element to be created should be a dict or list."""
    if name in LISTIFY:
        list_of_lists = LISTIFY[name]
        for tag_list in list_of_lists:
            if element_ancestors_match_list(parent_element, tag_list):
                return True
    return False


def element_to_json(name, element):
    if element_must_be_list(element, name):
        return element_to_list(element)
    else:
        return element_to_dict(element)

def root_element_to_json(name, element):
    """Returns a tuple of the root JSON value, plus the links if found."""
    if name == "rootEnabled": # Why oh why were we inconsistent here? :'(
        return bool(element.text), None
    elif element_must_be_list(element, name):
        return element_to_list(element, True)
    else:
        return element_to_dict(element), None


def element_to_list(element, check_for_links=False):
    """
    For element "foo" in <foos><foo/><foo/></foos>
    Returns [{}, {}]
    """
    links = None
    result = []
    for child_element in element:
        # The "links" element gets jammed into the root element.
        if check_for_links and normalize_tag(child_element) == "links":
            links = element_to_list(child_element)
        else:
            result.append(element_to_dict(child_element))
    if check_for_links:
        return result, links
    else:
        return result


def element_to_dict(element):
    result = {}
    for name, value in element.items():
        result[name] = value
    for child_element in element:
        name = normalize_tag(child_element)
        result[name] = element_to_json(name, child_element)
    return result


def standardize_json_lists(json_dict):
    """
    In XML, we might see something like {'instances':{'instances':[...]}},
    which we must change to just {'instances':[...]} to be compatable with
    the true JSON format.

    If any items are dictionaries with only one item which is a list,
    simply remove the dictionary and insert its list directly.
    """
    found_items = []
    for key, value in json_dict.items():
        value = json_dict[key]
        if isinstance(value, dict):
            if len(value) == 1 and isinstance(value.values()[0], list):
                found_items.append(key)
            else:
                standardize_json_lists(value)
    for key in found_items:
        json_dict[key] = json_dict[key].values()[0]


def normalize_tag(elem):
    """Given an element, returns the tag minus the XMLNS junk.

    IOW, .tag may sometimes return the XML namespace at the start of the
    string. This gets rids of that.
    """
    try:
        prefix = "{" + elem.nsmap[None] + "}"
        if elem.tag.startswith(prefix):
            return elem.tag[len(prefix):]
    except KeyError:
        pass
    return elem.tag


def create_root_xml_element(name, value):
    """Create the first element using a name and a dictionary."""
    element = etree.Element(name, nsmap=XML_NS)
    if name in REQUEST_AS_LIST:
        add_subelements_from_list(element, name, value)
    else:
        populate_element_from_dict(element, value)
    return element


def create_subelement(parent_element, name, value):
    """Attaches a new element onto the parent element."""
    if isinstance(value, dict):
        create_subelement_from_dict(parent_element, name, value)
    elif isinstance(value, list):
        create_subelement_from_list(parent_element, name, value)
    else:
        raise TypeError("Can't handle type %s." % type(value))


def create_subelement_from_dict(parent_element, name, dict):
    element = etree.SubElement(parent_element, name)
    populate_element_from_dict(element, dict)


def create_subelement_from_list(parent_element, name, list):
    element = etree.SubElement(parent_element, name)
    add_subelements_from_list(element, name, list)


def add_subelements_from_list(element, name, list):
    if name.endswith("s"):
        item_name = name[:len(name) - 1]
    else:
        item_name = name
    for item in list:
        create_subelement(element, item_name, item)


def populate_element_from_dict(element, dict):
    for key, value in dict.items():
        if isinstance(value, basestring):
            element.set(key, value)
        elif isinstance(value, Number):
            element.set(key, str(value))
        else:
            create_subelement(element, key, value)


class ReddwarfXmlClient(ReddwarfHTTPClient):

    @classmethod
    def morph_request(self, kwargs):
        kwargs['headers']['Accept'] = 'application/xml'
        kwargs['headers']['Content-Type'] = 'application/xml'
        if 'body' in kwargs:
            body = kwargs['body']
            root_name = body.keys()[0]
            xml = create_root_xml_element(root_name, body[root_name])
            xml_string = etree.tostring(xml, pretty_print=True)
            kwargs['body'] = xml_string

    @classmethod
    def morph_response_body(self, body_string):
        # The root XML element always becomes a dictionary with a single
        # field, which has the same key as the elements name.
        result = {}
        try:
            root_element = etree.XML(body_string)
        except etree.XMLSyntaxError:
            raise exceptions.ResponseFormatError()
        root_name = normalize_tag(root_element)
        root_value, links = root_element_to_json(root_name, root_element)
        result = { root_name:root_value }
        if links:
            result['links'] = links
        return result
