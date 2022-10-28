import os
import sys
import logging
import argparse
import getpass
 
msg = "Credentials for CSPC entered at runtime"
 
# Initialize parser
parser = argparse.ArgumentParser(description = msg)
parser.add_argument("-u", "--username", help = "CSPC Username", required=True)
parser.add_argument("-p", "--password", help = "CSPC PW")
args = parser.parse_args()

#Import cspc_api using the directory one level up as root
path = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(path)

from cspc_api import CspcApi

format = "%(asctime)s %(name)10s %(levelname)8s: %(message)s"
logfile="../cspc_update.log"
logging.basicConfig(format=format, level=logging.DEBUG, filename=logfile)


if not args.password:
    args.password = getpass.getpass()


cspc_user = args.username
cspc_pass = args.password


cspc = CspcApi('172.18.176.70', cspc_user, cspc_pass, verify=False)
print(cspc.get_devices(return_json=True))

devices = [
    { 
        'HostName': 'CAaaS_SW',     
        'IPAddress': '172.18.176.74', 
        'DomainName': 'testhostname1.example.com', 
        'PrimaryDeviceName': 'testhostname1.example.com',
    },
    { 
        'HostName': 'testhostname2', 
        'IPAddress': '1.2.3.5', 
        'DomainName': 'testhostname2.example.com', 
        'PrimaryDeviceName': 'testhostname2.example.com',
    },
]
print(cspc.add_multiple_devices(devices, return_json=True))

devices = {"testhostname1", "testhostname2"}
devices_to_del = cspc.get_devices_by(key="Id", value=devices)
print(cspc.delete_multiple_devices(devices_to_del, return_json=True))

discoverDevices = ['172.18.176.74','1.2.3.5']