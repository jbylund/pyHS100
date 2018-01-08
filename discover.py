from __future__ import absolute_import
import socket
import logging
import json
import time
from typing import Dict
import os
import sys
dirname = os.path.dirname(__file__)
sys.path.append(dirname)

from pyHS100 import TPLinkSmartHomeProtocol, SmartDevice, SmartPlug, SmartBulb

_LOGGER = logging.getLogger(__name__)


class Discover(object):
    @staticmethod
    def discover(protocol=None,
                 port=9999,
                 timeout=0.1):
        u"""
        Sends discovery message to 255.255.255.255:9999 in order
        to detect available supported devices in the local network,
        and waits for given timeout for answers from devices.

        :param protocol: Protocol implementation to use
        :param timeout: How long to wait for responses, defaults to 5
        :param port: port to send broadcast messages, defaults to 9999.
        :rtype: dict
        :return: Array of json objects {"ip", "port", "sys_info"}
        """
        if protocol is None:
            protocol = TPLinkSmartHomeProtocol()

        discovery_query = {
            u"emeter": {u"get_realtime": None},
            u"system": {u"get_sysinfo": None},
        }
        target = u"255.255.255.255"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(timeout)

        req = json.dumps(discovery_query)
        _LOGGER.debug(u"Sending discovery to %s:%s", target, port)

        encrypted_req = protocol.encrypt(req)
        sock.sendto(encrypted_req[4:], (target, port))

        devices = {}
        _LOGGER.debug(u"Waiting %s seconds for responses...", timeout)

        try:
            while True:
                data, addr = sock.recvfrom(4096)
                ip, port = addr
                info = json.loads(protocol.decrypt(data))
                if u"system" in info and u"get_sysinfo" in info[u"system"]:
                    sysinfo = info[u"system"][u"get_sysinfo"]
                    if u"type" in sysinfo:
                        type = sysinfo[u"type"]
                    elif u"mic_type" in sysinfo:
                        type = sysinfo[u"mic_type"]
                    else:
                        _LOGGER.error(u"Unable to find the device type field!")
                        type = u"UNKNOWN"
                else:
                    _LOGGER.error(u"No 'system' nor 'get_sysinfo' in response")
                if u"smartplug" in type.lower():
                    devices[ip] = SmartPlug(ip)
                elif u"smartbulb" in type.lower():
                    devices[ip] = SmartBulb(ip)
        except socket.timeout:
            _LOGGER.debug(u"Got socket timeout, which is okay.")
        except Exception, ex:
            _LOGGER.error(u"Got exception %s", ex, exc_info=True)
        return devices

def main():
    found = Discover.discover()
    print found.keys()

if "__main__" == __name__:
    main()
