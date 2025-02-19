#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import logging
import os
import sys
import time
from xml.etree import ElementTree
import requests
import xmltodict
import json

class CspcApi:

    xml_request_dir = os.path.join(os.path.realpath(
        os.path.dirname(__file__)), 'xml_requests')

    ElementTree.register_namespace('', 'http://www.parinetworks.com/api/schemas/1.1')

    def __init__(self, host, user, pwd, verify):
        '''

        Args:
            host (str): IP or hostname (without https://) of CSPC
            user (str): Username for ers API
            password (str): Password for ers API user
            verify (bool): enable / disable certificate check for requests to CSPC.
        '''

        self.logger = logging.getLogger('CspcApi')
        self.host = host + ':8001'
        self.user = user
        self.password = pwd
        self.creds = ':'.join([self.user, self.password])
        self.encodedAuth = base64.b64encode(self.creds.encode('utf-8'))

        if not verify:
            import urllib3
            urllib3.disable_warnings()

        self.headers = {
            'accept': 'application/xml',
            'Authorization': ' '.join(['Basic', self.encodedAuth.decode('utf-8')]),
            'cache-control': 'no-cache',
        }
        self.kwargs = {
            'verify': verify,
            'headers': self.headers
        }

    def __str__(self):
        return f"{type(self).__name__}(\"{self.host[:-5]}\", \"{self.user}\", \"{self.password}\", {self.kwargs['verify']})"

    def __eq__(self, other):
        return (self.host, self.user, self.password, self.kwargs['verify']) == (other.host, other.user, other.password, other.kwargs['verify'])
    
    def _info(self):
        """Performs get request to the CSPC info API endpoint

        Returns:
            str: response body of CSPC get /cspc/info
        """
        link = 'https://' + self.host + '/cspc/info'

        self.logger.debug('GET ' + link + '\nRequest Headers: ' + str(self.headers))
        response = requests.get(link, **self.kwargs)
        response_headers = response.headers
        self.logger.debug('Response Headers:\n' + str(response_headers))
        body = response.text
        self.logger.debug('Response Body:\n' + body)
        return body

    def _xml(self, payload):
        """ Performs POST xml request to CSPC

        Args:
            payload (str): string, use _get_xml_payload() to load content from `xml_request_dir`

        Returns:
            str: body of the CSPC response, usually an xml string

        Example:
            # Parse the body with ElementTree (from xml.etree import ElementTree) to proceed:
            payload = self._get_xml_payload('get_details_of_all_devices.xml')
            all_devices = self._xml(payload)
            tree = ElementTree.fromstring(all_devices)
        """
        link = 'https://' + self.host + '/cspc/xml'

        self.logger.debug('POST ' + link +
                          '\nRequest Headers: ' + str(self.headers) +
                          '\nRequest Body: ' + str(payload))
        response = requests.post(link, payload, **self.kwargs)
        response_headers = response.headers
        body = response.text
        self.logger.debug('Response Headers:\n' + str(response_headers))
        self.logger.debug('Response Body:\n' + body)
        if response.status_code != 200:
            raise RuntimeError(response)
        return body

    def _get_xml_payload(self, request_name):
        """Loads the full/skeleton xml request from an example file

        Args:
            payload (str): xml file in the `xml_request_dir`

        Returns:
            str: xml from file string
        """
        path = os.path.join(CspcApi.xml_request_dir, request_name)
        with open(path, 'r') as f:
            payload = f.read()
        return payload

    def list_xml_to_json_elem(self, list_of_xml: list):
        """Takes xml and returns json

        Args:
            elem_tree (xml.etree.ElementTree) : tree to search

        Returns:
            json: dict
        """
        json_data = []
        for xml in list_of_xml:
            json_data.append(self.xml_to_json_elem(xml))
        # convert into json
        temp = json.dumps(json_data, indent=2)
        final = json.loads(temp)
        return final
    
    def xml_to_json_elem(self, xml: ElementTree or str):
        """Takes xml and returns json

        Args:
            elem_tree (xml.etree.ElementTree) : tree to search

        Returns:
            dict: dict
        """
        xml_string = ElementTree.tostring(xml) if isinstance(xml, ElementTree.Element) else xml
        json_dict = (xmltodict.parse(xml_string))
        return json_dict


    def _get_xml_elem(self, path, elem_tree):
        """Loads the full/skeleton xml request from an example file

        Args:
            path (str): tag name to search for
            elem_tree (xml.etree.ElementTree) : tree to search

        Returns:
            xml.etree.Element: first element matched by tagname
        """
        # https://docs.python.org/3/library/xml.etree.elementtree.html
        # xml library will prefix all elements with their NS from a parsed file.
        ns = {
            'ns': 'http://www.parinetworks.com/api/schemas/1.1'
        }
        return elem_tree.find(f'.//ns:{path}', namespaces=ns)


    def send_and_import_seed_file_csv(self, csv, device_group_name):
        """ upload seedfile to CSPC

        Args:
            csv (str): csv formatted list of devices to add
            device_group_name (str): can be empty string

        Returns:
            str: body of the CSPC response
        """
        seed_file_name = f'{device_group_name}-{time.strftime("%Y%m%d-%H%M%S")}.csv'
        xmlrequest = f"""
        <Request>
            <Job>
                <Schedule operationId="1">
                <JobSchedule runnow="true"/>
                <ImportSeedFileJob jobName="testimport">
                    <Description>Import SeedFile Job </Description>
                    <DeviceGroup>{device_group_name}</DeviceGroup>
                    <SeedFileDescr>cnc seed file</SeedFileDescr>
                    <SeedFileFormat>CISCO_CNC_CSV</SeedFileFormat>
                    <FileDetails>
                    <SeedFileName>{seed_file_name}</SeedFileName>
                    </FileDetails>
                    <TriggerDiscovery>true</TriggerDiscovery>
                    <TriggerDav>false</TriggerDav>
                </ImportSeedFileJob>
                </Schedule>
            </Job>
        </Request>
        """

        link = 'https://' + self.host + '/cspc/seedfile'

        files = {'request': (None, xmlrequest.encode('utf8')), 'file': (
            seed_file_name, csv.encode('utf8'))}

        response = requests.post(link, files=files, headers=self.headers, verify=False)

        self.logger.debug('POST ' + link +
                          '\nRequest Headers: ' + str(self.headers) +
                          '\nRequest Body: ' + str(files))

        response_headers = response.headers
        self.logger.debug('Response Headers:\n' + str(response_headers))
        body = response.text
        self.logger.debug('Response Body:\n' + body)

        return body

    def get_devices(self, return_json=False):
        """returns an array of dict with all registered devices
        Returns:
            list: of XML Elements

        Example:
        ```
            <Device>
                <Id>31591</Id>
                <HostName>switch1</HostName>
                <IPAddress>172.16.2.112</IPAddress>
                <Status>Reachable</Status>
                <DeviceFamily>LANSwitches</DeviceFamily>
                <ProductFamily><![CDATA[Cisco Catalyst 2960-S Series Switches]]></ProductFamily>
                <Model>cat29xxStack</Model>
                <SerialNumber>S/N discovery disabled</SerialNumber>
                <Vendor>Cisco Systems Inc.</Vendor>
                <OS>IOS</OS>
                <Version>15.2(4)E7</Version>
                <Image></Image>
                <DiscTime>1600812032000</DiscTime>
                <InvTime>1600812032634</InvTime>
                <SysObjectId>.1.3.6.1.4.1.9.1.1208</SysObjectId>
                <SysLocation><![CDATA[Company1 3rd Floor]]></SysLocation>
                <SysDescription><![CDATA[Cisco IOS Software, C2960X Software (C2960X-UNIVERSALK9-M), Version 15.2(4)E7, RELEASE SOFTWARE (fc2)  Technical Support: http://www.cisco.com/techsupport  Copyright (c) 1986-2018 by Cisco Systems, Inc.  Compiled Tue 18-Sep-18 13:07 by prod_rel_team]]></SysDescription>
                <DomainName>infra.example.com</DomainName>
                <DeviceSource>10.0.0.10</DeviceSource>
                <PrimaryDeviceName><![CDATA[switch1.infra.example.com]]></PrimaryDeviceName>
                <SysName><![CDATA[switch1.infra.example.com]]></SysName>
            </Device>
        ```
        """
        all_devices = self._xml(self._get_xml_payload('get_details_of_all_devices.xml'))
        tree = ElementTree.fromstring(all_devices)
        devices = tree.findall('.//Device')

        self.logger.info('num devices: ' + str(len(devices)))
        if return_json:
            devices = self.list_xml_to_json_elem(devices)
        return devices

    def get_unreachable_devices(self):
        """returns an array of dict with unreachable devices

        Returns:
            list: of device dictionariers with keys: Id, HostName, IPAddress, Status
        """
        devices = self.get_devices()

        self.logger.info('num devices: ' + str(len(devices)))
        unreachable_devices = []
        for elem in devices:
            if elem.findtext('Status').lower() != 'reachable':
                dev_dict = {
                    'Id': str(elem.findtext('Id')),
                    'HostName': str(elem.findtext('HostName')),
                    'IPAddress': str(elem.findtext('IPAddress')),
                    'Status': str(elem.findtext('Status'))
                }
                unreachable_devices.append(dev_dict)
                # print(dev_dict)
        return unreachable_devices

    def _check_in_str(self, string_to_check, check: str or set):
        if isinstance(check, str):
            return check in string_to_check
        return any(item in string_to_check for item in check)
    
    def get_devices_by(self, key="HostName", value=None):
        """returns an array of dict with devices where the text attribute of the key element matches (case-sensitive) 
        the given value with python 'in' operator

        i.e. if value in device<key>...

        For list of possible keys see #get_devices
        
        Args:
            key (str): tag name to match
            value (str):  tag contents to match against

        Returns:
            list: of device dictionariers with all keys from #get_devices

        Example:
        ```
            # find all devices having 1.2.3. in their IP address
            my_devices = cspc.get_devices_by('IPAddress', '1.2.3.')
        ```
        """
        #list of element tree objects
        devices = self.get_devices()
        self.logger.info('num devices: ' + str(len(devices)))
        matched_devices = []
        for device in devices:
            if self._check_in_str(device.findtext(key), value):
                device_dict = {}
                for child in device:
                    device_dict[child.tag] =  str(device.findtext(child.tag))
                matched_devices.append(device_dict)
        return matched_devices


    def _add_elem_with_text(self, tag, text, parent):
        d = ElementTree.Element(tag)
        d.text = text
        parent.append(d)
        return d

    def add_multiple_device_credentials_snmpv2c(self, credentials, return_json=False):
        """Adds snmpv2c credentials for multiple devices by IP expression

        Args:
            credentials (dict): key = credential_name, value = dict(ip_expression=, snmp_read_community=, snmp_write_community=)

        Returns:
            str: Response of CSPC

        Example:
            This is an example payload for snmp or telnet credentials:
            ```<DeviceCredential identifier="My_snmpv1_1">
                <Protocol>snmpv1</Protocol>
                <WriteCommunity>private</WriteCommunity>
                <IpExpressionList>
                    <IpExpression>*.*.*.*</IpExpression>
                </IpExpressionList>
                <ExcludeIpExprList>
                    <IpExpression>192.168.*.*IpExpression>
                </ExcludeIpExprList>
            </DeviceCredential>
            <DeviceCredential identifier="My_telnet_1">
                <Protocol>telnet</Protocol>
                <UserName>admin</UserName>
                <Password>admin</Password>
                <EnableUserName>testuser</EnableUserName>
                <EnablePassword>testpass</EnablePassword>
                <IpExpressionList>
                    <IpExpression>*.*.*.*</IpExpression>
                    <IpExpression>FE80::0009</IpExpression>
                </IpExpressionList>
                <ExcludeIpExprList>
                    <IpExpression>192.168.0.*</IpExpression>
                </ExcludeIpExprList>
            </DeviceCredential>
            ```
        """
        tree = ElementTree.fromstring(self._get_xml_payload('add_multiple_device_credentials.xml'))

        cred_list = self._get_xml_elem('DeviceCredentialList', tree)
        for cred_name, creds in credentials.items():
            # SNMPv2c credential
            device_credential = ElementTree.Element('DeviceCredential', identifier=cred_name)
            self._add_elem_with_text('Protocol', 'snmpv2c', device_credential)
            self._add_elem_with_text('ReadCommunity', creds['snmp_read_community'], device_credential)
            self._add_elem_with_text('WriteCommunity',creds['snmp_write_community'], device_credential)
            ip_expr = ElementTree.Element('IpExpressionList')
            self._add_elem_with_text('IpExpression', creds['ip_expression'], ip_expr)
            device_credential.append(ip_expr)
            cred_list.append(device_credential)
        request = self._xml(ElementTree.tostring(tree, encoding='unicode'))
        if return_json:
            #pass string to xml to json >> dict >> str
            return json.dumps(self.xml_to_json_elem(request))
        return request

    def add_multiple_device_credentials_ssh(self, credentials, return_json=False):
        """Adds sshv2 credentials for multiple devices by IP expression

        Args:
            credentials (dict): key = credential_name, value = dict(ip_expression=, user=, password=, enable_password=)

        Returns:
            str: Response of CSPC

        Example:
            This is an example payload for snmp or telnet credentials:
            ```<DeviceCredential identifier="My_snmpv1_1">
                <Protocol>snmpv1</Protocol>
                <WriteCommunity>private</WriteCommunity>
                <IpExpressionList>
                    <IpExpression>*.*.*.*</IpExpression>
                </IpExpressionList>
                <ExcludeIpExprList>
                    <IpExpression>192.168.*.*IpExpression>
                </ExcludeIpExprList>
            </DeviceCredential>
            <DeviceCredential identifier="My_telnet_1">
                <Protocol>telnet</Protocol>
                <UserName>admin</UserName>
                <Password>admin</Password>
                <EnableUserName>testuser</EnableUserName>
                <EnablePassword>testpass</EnablePassword>
                <IpExpressionList>
                    <IpExpression>*.*.*.*</IpExpression>
                    <IpExpression>FE80::0009</IpExpression>
                </IpExpressionList>
                <ExcludeIpExprList>
                    <IpExpression>192.168.0.*</IpExpression>
                </ExcludeIpExprList>
            </DeviceCredential>
            ```
        """
        tree = ElementTree.fromstring(self._get_xml_payload('add_multiple_device_credentials.xml'))

        cred_list = self._get_xml_elem('DeviceCredentialList', tree)
        for cred_name, creds in credentials.items():
            # SSHv2 credential
            device_credential = ElementTree.Element('DeviceCredential', identifier=cred_name)
            self._add_elem_with_text('Protocol', 'sshv2', device_credential)
            self._add_elem_with_text('UserName', creds['user'], device_credential)
            self._add_elem_with_text('Password', creds['password'], device_credential)
            self._add_elem_with_text('EnablePassword', creds['enable_password'], device_credential)
            ip_expr = ElementTree.Element('IpExpressionList')
            self._add_elem_with_text('IpExpression', creds['ip_expression'], ip_expr)
            device_credential.append(ip_expr)
            cred_list.append(device_credential)
        request = self._xml(ElementTree.tostring(tree, encoding='unicode'))
        if return_json:
            #pass string to xml to json >> dict >> str
            return json.dumps(self.xml_to_json_elem(request))
        return request


    def add_multiple_devices(self, devices, return_json=False):
        """Adds multiple devices to CSPC.

        Note: By default the IP Address is chosen as PrimaryDeviceName. PrimaryDeviceName is used
        as 'Hostname' key by other Cisco Tools (SNTC, BCS). So if you need Hostname or FQDN name in
        those tools, please specify the PrimaryDeviceName.

        Args:
            devices (list<dict>): list of device dictionaries. For valid keys see :func: `<get_devices>`
            at minimum IPAddress is required.

        Returns:
            str: Response of CSPC

        See also: examples/add_devices_and_credentials.py
        """
        tree = ElementTree.fromstring(self._get_xml_payload('add_multiple_devices.xml'))
        device_list = self._get_xml_elem('DeviceList', tree)
        for device in devices:
            elem = ElementTree.Element('Device')
            for tag, value in device.items():
                d = ElementTree.Element(tag)
                d.text = value
                elem.append(d)

            device_list.append(elem)
        request = self._xml(ElementTree.tostring(tree, encoding='unicode'))
        if return_json:
            #pass string to xml to json >> dict >> str
            return json.dumps(self.xml_to_json_elem(request))
        return request

    def discover_multiple_devices(self, ips, return_json=False):
        ts = time.time()
        tree = ElementTree.fromstring(self._get_xml_payload('discover_multiple_devices.xml'))
        device_list = self._get_xml_elem('IPAddressList', tree)
        job = self._get_xml_elem('DiscoveryJob', tree)
        job.set('identifier', str(int(ts)))
        for ip in ips:
            elem = ElementTree.Element('IPAddress')
            elem.text = ip
            device_list.append(elem)
        request = self._xml(ElementTree.tostring(tree, encoding='unicode'))
        if return_json:
            return json.dumps(self.xml_to_json_elem(request))
        return request

    def delete_multiple_devices(self, device_array, return_json = False):
        """ Deletes multiple devices by ID from CSPC

        Args:
            device_array (list): list of dictionaries, as returned by :func: `<unreachable_devices>`

        Returns:
            str: Response of CSPC
        """
        tree = ElementTree.fromstring(self._get_xml_payload('delete_multiple_devices.xml'))
        device_list = self._get_xml_elem('DeviceList', tree)
        for dev in device_array:
            elem = ElementTree.Element('Device')
            d = ElementTree.Element('Id')
            d.text = dev['Id']
            elem.append(d)
            device_list.append(elem)
        request = self._xml(ElementTree.tostring(tree, encoding='unicode'))
        if return_json:
            #pass string to xml to json >> dict >> str
            return json.dumps(self.xml_to_json_elem(request))
        return request

    def get_formatted_csv_device_entry(self, ipaddress, hostname='', username='', password='', enable_password='', snmp_v2_RO='', snmp_v2_RW=''):
        """
        Returns:
            str: single line of csv including trailing newline '\\n'

        """
        col1_IP_Address_including_domain_or_simply_an_IP = ipaddress
        col2_Host_Name = hostname
        col3_Domain_Name = ''
        col4_Device_Identity = ''
        col5_Display_Name = ''
        col6_SysObjectID = ''
        col7_DCR_Device_Type = ''
        col8_MDF_Type = ''
        col9_Snmp_RO = snmp_v2_RO
        col10_Snmp_RW = snmp_v2_RW
        col11_SnmpV3_User_Name = ''  # TODO
        col12_Snmp_V3_Auth_Pass = ''  # TODO
        col13_Snmp_V3_Engine_ID = ''  # TODO
        col14_Snmp_V3_Auth_Algorithm = ''  # TODO
        col15_RX_Boot_Mode_User = ''
        col16_RX_Boot_Mode_Pass = ''
        col17_Primary_User_Tacacs_User = username
        col18_Primary_Pass_Tacacs_Pass = password
        col19_Primary_Enable_Pass = enable_password
        col20_Http_User = ''  # TODO
        col21_Http_Pass = ''  # TODO
        col22_Http_Mode = ''  # TODO
        col23_Http_Port = ''  # TODO
        col24_Https_Port = ''  # TODO
        col25_Cert_Common_Name = ''
        col26_Secondary_User = ''
        col27_Secondary_Pass = ''
        col28_Secondary_Enable_Pass = ''
        col29_Secondary_Http_User = ''
        col30_Secondary_Http_Pass = ''
        col31_Snmp_V3_Priv_Algorithm = ''  # TODO
        col32_Snmp_V3_Priv_Pass = ''  # TODO
        col33_User_Field_1 = ''
        col34_User_Field_2 = ''
        col35_User_Field_3 = ''
        col36_User_Field_4 = ''

        return f'{col1_IP_Address_including_domain_or_simply_an_IP},{col2_Host_Name},{col3_Domain_Name},{col4_Device_Identity},{col5_Display_Name},{col6_SysObjectID},{col7_DCR_Device_Type},{col8_MDF_Type},{col9_Snmp_RO},{col10_Snmp_RW},{col11_SnmpV3_User_Name},{col12_Snmp_V3_Auth_Pass},{col13_Snmp_V3_Engine_ID},{col14_Snmp_V3_Auth_Algorithm},{col15_RX_Boot_Mode_User},{col16_RX_Boot_Mode_Pass},{col17_Primary_User_Tacacs_User},{col18_Primary_Pass_Tacacs_Pass},{col19_Primary_Enable_Pass},{col20_Http_User},{col21_Http_Pass},{col22_Http_Mode},{col23_Http_Port},{col24_Https_Port},{col25_Cert_Common_Name},{col26_Secondary_User},{col27_Secondary_Pass},{col28_Secondary_Enable_Pass},{col29_Secondary_Http_User},{col30_Secondary_Http_Pass},{col31_Snmp_V3_Priv_Algorithm},{col32_Snmp_V3_Priv_Pass},{col33_User_Field_1},{col34_User_Field_2},{col35_User_Field_3},{col36_User_Field_4}\n'


def _setup_logging():
    format = "%(asctime)s %(name)10s %(levelname)8s: %(message)s"
    # logfile='cspc.log'
    logfile = None
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S", filename=logfile)


if __name__ == '__main__':
    _setup_logging()
    if 'CSPC_USER' not in os.environ or 'CSPC_PASSWORD' not in os.environ:
        exit('make sure environment variables `CSPC_USER` and `CSPC_PASSWORD` are defined')
    if len(sys.argv) != 2:
        exit(f'usage: ./{sys.argv[0]} CSPC_IP')

    c = CspcApi(f'{sys.argv[1]}:8001', os.environ.get(
        'CSPC_USER'), os.environ.get('CSPC_PASSWORD'), verify=False)
    c._info()
    # print(os.path.realpath(__file__))
    u = c.get_unreachable_devices()
