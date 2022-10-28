import os
import sys

path = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(path)

from cspc_api import CspcApi
from xml.etree import ElementTree

def discover_devices(deviceIps):
    tree = ElementTree.fromstring(cspc._get_xml_payload('discover_multiple_devices.xml'))
    device_list = cspc._get_xml_elem('IPAddressList', tree)
    for ip in deviceIps:
        elem = ElementTree.Element('IPAddress')
        elem.text = ip
        device_list.append(elem)
    print(ElementTree.tostring(tree, encoding='unicode'))
    

cspc = CspcApi('172.18.176.70', "admin", "Admin#1234", verify=False)

deviceIpList = ['192.168.1.1', '192.168.1.100', '192.168.1.2']

discover_devices(deviceIpList)
