import unittest2
from lxml import etree
from reddwarfclient import xml


class XmlTest(unittest2.TestCase):
    
    ELEMENT = '''
        <instances>
            <instance>
                <flavor>
                    <links>
                    </links>
                    <value value="5"/>
                </flavor>
            </instance>
        </instances>
    '''
    ROOT = etree.fromstring(ELEMENT)
    
    JSON = {'instances': {'instances': ['1', '2', '3']}, 'dummy': {'dict': True}}
    
    def test_element_ancestors_match_list(self):
        # Test normal operation:
        self.assertTrue(xml.element_ancestors_match_list(self.ROOT[0][0], ['instance', 'instances']))
        
        # Test itr_elem is None:
        self.assertTrue(xml.element_ancestors_match_list(self.ROOT, ['instances']))
        
        # Test that the first parent element does not match the first list 
        # element:
        self.assertFalse(xml.element_ancestors_match_list(self.ROOT[0][0], ['instances', 'instance']))
        
    def test_element_must_be_list(self):
        # Test for when name isn't in the dictionary
        self.assertFalse(xml.element_must_be_list(self.ROOT, "not_in_list"))
        
        # Test when name is in the dictionary but list is empty
        self.assertTrue(xml.element_must_be_list(self.ROOT, "accounts"))

        # Test when name is in the dictionary but list is not empty
        self.assertTrue(xml.element_must_be_list(self.ROOT[0][0][0], "links"))

    def test_element_to_json(self):
        # Test when element must be list:
        self.assertEqual([{'flavor': {'links': [], 'value': {'value': '5'}}}], xml.element_to_json("accounts", self.ROOT))
        
        # Test when element must not be list:
        self.assertEqual({'instance': {'flavor': {'links': [], 'value': {'value': '5'}}}}, xml.element_to_json("not_in_list", self.ROOT))
        
    def test_root_element_to_json(self):
        # Test when element must be list:
        self.assertEqual(([{'flavor': {'links': [], 'value': {'value': '5'}}}], None), xml.root_element_to_json("accounts", self.ROOT))
        
        # Test when element must not be list:
        self.assertEqual(({'instance': {'flavor': {'links': [], 'value': {'value': '5'}}}}, None), xml.root_element_to_json("not_in_list", self.ROOT))
        
        # Test rootEnabled:
        self.assertEqual((True, None), xml.root_element_to_json("rootEnabled", self.ROOT))        

    def test_element_to_list(self):
        # Test w/ no child elements
        self.assertEqual([], xml.element_to_list(self.ROOT[0][0][0]))
        
        # Test w/ no child elements and check_for_links = True
        self.assertEqual(([], None), xml.element_to_list(self.ROOT[0][0][0], check_for_links=True))
        
        # Test w/ child elements
        self.assertEqual([{}, {'value': '5'}], xml.element_to_list(self.ROOT[0][0]))
        
        # Test w/ child elements and check_for_links = True
        self.assertEqual(([{'value': '5'}], []), xml.element_to_list(self.ROOT[0][0], check_for_links=True))
        
    def test_element_to_dict(self):
        self.assertEqual({'instance': {'flavor': {'links': [], 'value': {'value': '5'}}}}, xml.element_to_dict(self.ROOT))
        
    def test_standarize_json(self):
        xml.standardize_json_lists(self.JSON)
        self.assertEqual({'instances': ['1', '2', '3'], 'dummy': {'dict': True}}, self.JSON)
        
    def test_normalize_tag(self):
        ELEMENT_NS = '''
            <instances xmlns="http://www.w3.org/1999/xhtml">
                <instance>
                    <flavor>
                        <links>
                        </links>
                        <value value="5"/>
                    </flavor>
                </instance>
            </instances>
        '''
        ROOT_NS = etree.fromstring(ELEMENT_NS)
        
        # Test normalizing without namespace info
        self.assertEqual('instances', xml.normalize_tag(self.ROOT))
        
        # Test normalizing with namespace info
        self.assertEqual('instances', xml.normalize_tag(ROOT_NS))
        
    def test_create_root_xml_element(self):
        # Test creating when name is not in REQUEST_AS_LIST
        element = xml.create_root_xml_element("root", {"root": "value"})
        self.assertEqual('<root xmlns="http://docs.openstack.org/database/api/v1.0" root="value"/>', etree.tostring(element))
        
        # Test creating when name is in REQUEST_AS_LIST
        element = xml.create_root_xml_element("users", [])
        self.assertEqual('<users xmlns="http://docs.openstack.org/database/api/v1.0"/>', etree.tostring(element))

    def test_creating_subelements(self):
        # Test creating a subelement as a dictionary
        element = xml.create_root_xml_element("root", {"root": 5})
        xml.create_subelement(element, "subelement", {"subelement": "value"})
        self.assertEqual('<root xmlns="http://docs.openstack.org/database/api/v1.0" root="5"><subelement subelement="value"/></root>', etree.tostring(element))
        
        # Test creating a subelement as a list
        element = xml.create_root_xml_element("root", {"root": {"value": "nested"}})
        xml.create_subelement(element, "subelement", [{"subelement": "value"}])
        self.assertEqual('<root xmlns="http://docs.openstack.org/database/api/v1.0"><root value="nested"/><subelement><subelement subelement="value"/></subelement></root>', etree.tostring(element))
        
        # Test creating a subelement as a string (should raise TypeError)
        element = xml.create_root_xml_element("root", {"root": "value"})
        with self.assertRaises(TypeError):
            xml.create_subelement(element, "subelement", ["value"])

    def test_reddwarfxmlclient(self):
        from reddwarfclient import exceptions
        
        client = xml.ReddwarfXmlClient("user", "password", "tenant", "auth_url", "service_name", auth_strategy="fake")
        request = {'headers': {}}
        
        # Test morph_request, no body
        client.morph_request(request)
        self.assertEqual('application/xml', request['headers']['Accept'])
        self.assertEqual('application/xml', request['headers']['Content-Type'])
        
        # Test morph_request, with body
        request['body'] = {'root': {'test': 'test'}}
        client.morph_request(request)
        self.assertEqual({'body': '<root xmlns="http://docs.openstack.org/database/api/v1.0" test="test"/>\n', 'headers': {'Content-Type': 'application/xml', 'Accept': 'application/xml'}}, request)
        
        # Test morph_response_body
        request = "<users><links><user href='value'/></links></users>"
        result = client.morph_response_body(request)
        self.assertEqual({'users': [], 'links': [{'href': 'value'}]}, result)
        
        # Test morph_response_body with improper input
        with self.assertRaises(exceptions.ResponseFormatError):
            client.morph_response_body("value")

        
        
        
        
        