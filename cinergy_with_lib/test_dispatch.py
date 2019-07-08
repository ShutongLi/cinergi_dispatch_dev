import unittest
from dispatch import *
import lxml
from lxml import etree
from Distribution import DistObj
import json


class TestDispatch(unittest.TestCase):

    def setUp(self):
        self.md_url = 'http://datadiscoverystudio.org/geoportal/rest/metadata/item/e3619c5df2644204b67f51f48525a0b1/xml'
        self.tree = etree.parse(self.md_url)
        self.dist_list = get_distributions(self.tree)

    def test_construct_url(self):
        self.assertEqual(construct_md_url(100),
                         "http://datadiscoverystudio.org/geoportal/rest/metadata/item/100/xml")

    def test_test_url(self):
        self.assertFalse(testurl('not a url'))
        self.assertTrue(testurl('www.google.com'))

    def test_etree(self):
        md_url = 'http://datadiscoverystudio.org/geoportal/rest/metadata/item/e3619c5df2644204b67f51f48525a0b1/xml'
        self.assertIsInstance(get_etree(md_url), lxml.etree._ElementTree, 'does not return a etree')

    def test_get_dist(self):
        dist_list = get_distributions(self.tree)
        json_dump_str = json.dumps([theobj.dump() for theobj in dist_list])
        expected = '[{"adistobj": {"name": "Service Description", "url": "http://web2.nbmg.unr.edu/ArcGIS/services/CO_Data/COActiveFaults/MapServer/WMSServer?request=GetCapabilities&service=WMS", "description": "parameters:{layers:\\"ActiveFault\\"}", "protocol": "OGC:WMS", "appprofile": "", "functioncode": "381", "functiontext": "webService", "distorg": "Colorado Geological Survey", "formatlist": []}}, {"adistobj": {"name": "WFS Capabilities", "url": "http://web2.nbmg.unr.edu/ArcGIS/services/CO_Data/COActiveFaults/MapServer/WFSServer?request=GetCapabilities&service=WFS", "description": "parameters:{typeName:\\"ActiveFault\\"}", "protocol": "OGC:WFS", "appprofile": "", "functioncode": "381", "functiontext": "webService", "distorg": "Colorado Geological Survey", "formatlist": []}}, {"adistobj": {"name": "ESRI Service Endpoint", "url": "http://web2.nbmg.unr.edu/ArcGIS/rest/services/CO_Data/COActiveFaults/MapServer", "description": "", "protocol": "ESRI", "appprofile": "", "functioncode": "381", "functiontext": "webService", "distorg": "Colorado Geological Survey", "formatlist": []}}, {"adistobj": {"name": "Zipped Excel Workbook containing Active Faults Data for the State of Colorado", "url": "http://repository.stategeothermaldata.org/metadata/record/9e15e1a59b768b330d029e86dc1a10a1/file/activefaults_20131011repo.zip", "description": "", "protocol": "", "appprofile": "", "functioncode": "375", "functiontext": "download", "distorg": "Colorado Geological Survey", "formatlist": []}}, {"adistobj": {"name": "NGDS RSS feed for services notifications", "url": "http://notifications.usgin.org/", "description": "", "protocol": "", "appprofile": "", "functioncode": "375", "functiontext": "download", "distorg": "Colorado Geological Survey", "formatlist": []}}]'
        for dist in dist_list:
            self.assertIsInstance(dist,
                                  DistObj,
                                  'element in the dist_list is not an instance of DistObj from Distribution.py')
        self.assertEqual(json_dump_str, expected)

    # pre-condition: dist_to_tokens take in a list of n distribution objects (n >= 0)
    # given there are m functions, the resulting list should be a list of m*n elements
    def test_dists_to_tokens(self):
        dist_list_empty = []
        result_empty = dists_to_token(dist_list_empty)
        expected_empty = {}
        self.assertEqual(result_empty, expected_empty)
        dist_list_all_wrong = [DistObj('WHAAAT')]
        result_all_wrong = dists_to_token(dist_list_all_wrong)
        expected_all_wrong = [{} for i in range(len(tbl1['expression'].dropna))]
        self.assertEqual(result_all_wrong, expected_all_wrong)

    # Below logic for data structure manipulation
    def test_combine_dicts(self):
        dct1 = {'a': 1}
        dct2 = {'a': 2}
        result = combine_dcts([dct1, dct2])
        expected = {'a': [1, 2]}
        self.assertEqual(result, expected)

    def test_url_template(self):
        template = 'http://suave-jupyterhub.com/user/zeppelin-v/notebooks/DispatchTesting/NWIS-explore2.ipynb?dataurl={dataURL}'
        dist_url= 'tada'
        result = token_url_template(template, dist_url)
        expect = 'http://suave-jupyterhub.com/user/zeppelin-v/notebooks/DispatchTesting/NWIS-explore2.ipynb?dataurl=tada'
        self.assertEqual(result, expect)


if __name__ == '__main__':
    unittest.main()