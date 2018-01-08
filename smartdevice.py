u"""
pyHS100
Python library supporting TP-Link Smart Plugs/Switches (HS100/HS110/Hs200).

The communication protocol was reverse engineered by Lubomir Stroetmann and
Tobias Esser in 'Reverse Engineering the TP-Link HS110':
https://www.softscheck.com/en/reverse-engineering-tp-link-hs110/

This library reuses codes and concepts of the TP-Link WiFi SmartPlug Client
at https://github.com/softScheck/tplink-smartplug, developed by Lubomir
Stroetmann which is licensed under the Apache License, Version 2.0.

You may obtain a copy of the license at
http://www.apache.org/licenses/LICENSE-2.0
"""
from __future__ import absolute_import
import datetime
import logging
import socket
import warnings
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Optional

from .protocol import TPLinkSmartHomeProtocol

_LOGGER = logging.getLogger(__name__)


class SmartDeviceException(Exception):
    u"""
    SmartDeviceException gets raised for errors reported by device.
    """
    pass


class SmartDevice(object):
    # possible device features
    FEATURE_ENERGY_METER = u'ENE'
    FEATURE_TIMER = u'TIM'

    ALL_FEATURES = (FEATURE_ENERGY_METER, FEATURE_TIMER)

    def __init__(self,
                 ip_address,
                 protocol=None):
        u"""
        Create a new SmartDevice instance, identified through its IP address.

        :param str ip_address: ip address on which the device listens
        """
        socket.inet_pton(socket.AF_INET, ip_address)
        self.ip_address = ip_address
        if not protocol:
            protocol = TPLinkSmartHomeProtocol()
        self.protocol = protocol
        self.emeter_type = u"emeter"  # type: str
        self.emeter_units = False

    def _query_helper(self,
                      target,
                      cmd,
                      arg=None):
        u"""
        Helper returning unwrapped result object and doing error handling.

        :param target: Target system {system, time, emeter, ..}
        :param cmd: Command to execute
        :param arg: JSON object passed as parameter to the command
        :return: Unwrapped result for the call.
        :rtype: dict
        :raises SmartDeviceException: if command was not executed correctly
        """
        if arg is None:
            arg = {}
        try:
            response = self.protocol.query(
                host=self.ip_address,
                request={target: {cmd: arg}}
            )
        except Exception, ex:
            raise SmartDeviceException(u'Communication error')

        if target not in response:
            raise SmartDeviceException(u"No required {} in response: {}"
                                       .format(target, response))

        result = response[target]
        if u"err_code" in result and result[u"err_code"] != 0:
            raise SmartDeviceException(u"Error on {}.{}: {}"
                                       .format(target, cmd, result))

        result = result[cmd]
        del result[u"err_code"]

        return result

    @property
    def features(self):
        u"""
        Returns features of the devices

        :return: list of features
        :rtype: list
        """
        warnings.simplefilter(u'always', DeprecationWarning)
        warnings.warn(
            u"features works only on plugs and its use is discouraged, "
            u"and it will likely to be removed at some point",
            DeprecationWarning,
            stacklevel=2
        )
        warnings.simplefilter(u'default', DeprecationWarning)
        if u"feature" not in self.sys_info:
            return []

        features = self.sys_info[u'feature'].split(u':')

        for feature in features:
            if feature not in SmartDevice.ALL_FEATURES:
                _LOGGER.warning(u"Unknown feature %s on device %s.",
                                feature, self.model)

        return features

    @property
    def has_emeter(self):
        u"""
        Checks feature list for energy meter support.
        Note: this has to be implemented on a device specific class.

        :return: True if energey meter is available
                 False if energymeter is missing
        """
        raise NotImplementedError()

    @property
    def sys_info(self):
        u"""
        Returns the complete system information from the device.

        :return: System information dict.
        :rtype: dict
        """
        return defaultdict(lambda: None, self.get_sysinfo())

    def get_sysinfo(self):
        u"""
        Retrieve system information.

        :return: sysinfo
        :rtype dict
        :raises SmartDeviceException: on error
        """
        return self._query_helper(u"system", u"get_sysinfo")

    def identify(self):
        u"""
        Query device information to identify model and featureset

        :return: (alias, model, list of supported features)
        :rtype: tuple
        """
        warnings.simplefilter(u'always', DeprecationWarning)
        warnings.warn(
            u"use alias and model instead of idenfity()",
            DeprecationWarning,
            stacklevel=2
        )
        warnings.simplefilter(u'default', DeprecationWarning)

        info = self.sys_info

        #  TODO sysinfo parsing should happen in sys_info
        #  to avoid calling fetch here twice..
        return info[u"alias"], info[u"model"], self.features

    @property
    def model(self):
        u"""
        Get model of the device

        :return: device model
        :rtype: str
        :raises SmartDeviceException: on error
        """
        return unicode(self.sys_info[u'model'])

    @property
    def alias(self):
        u"""
        Get current device alias (name)

        :return: Device name aka alias.
        :rtype: str
        """
        return unicode(self.sys_info[u'alias'])

    @alias.setter
    def alias(self, alias):
        u"""
        Sets the device name aka alias.

        :param alias: New alias (name)
        :raises SmartDeviceException: on error
        """
        self._query_helper(u"system", u"set_dev_alias", {u"alias": alias})

    @property
    def icon(self):
        u"""
        Returns device icon

        Note: not working on HS110, but is always empty.

        :return: icon and its hash
        :rtype: dict
        :raises SmartDeviceException: on error
        """
        return self._query_helper(u"system", u"get_dev_icon")

    @icon.setter
    def icon(self, icon):
        u"""
        Content for hash and icon are unknown.

        :param str icon: Icon path(?)
        :raises NotImplementedError: when not implemented
        :raises SmartPlugError: on error
        """
        raise NotImplementedError()
        # here just for the sake of completeness
        # self._query_helper("system",
        #                    "set_dev_icon", {"icon": "", "hash": ""})
        # self.initialize()

    @property
    def time(self):
        u"""
        Returns current time from the device.

        :return: datetime for device's time
        :rtype: datetime.datetime or None when not available
        :raises SmartDeviceException: on error
        """
        try:
            res = self._query_helper(u"time", u"get_time")
            return datetime.datetime(res[u"year"], res[u"month"], res[u"mday"],
                                     res[u"hour"], res[u"min"], res[u"sec"])
        except SmartDeviceException:
            return None

    @time.setter
    def time(self, ts):
        u"""
        Sets time based on datetime object.
        Note: this calls set_timezone() for setting.

        :param datetime.datetime ts: New date and time
        :return: result
        :type: dict
        :raises NotImplemented: when not implemented.
        :raises SmartDeviceException: on error
        """
        raise NotImplementedError(u"Fails with err_code == 0 with HS110.")
        u"""
        here just for the sake of completeness.
        if someone figures out why it doesn't work,
        please create a PR :-)
        ts_obj = {
            "index": self.timezone["index"],
            "hour": ts.hour,
            "min": ts.minute,
            "sec": ts.second,
            "year": ts.year,
            "month": ts.month,
            "mday": ts.day,
        }


        response = self._query_helper("time", "set_timezone", ts_obj)
        self.initialize()

        return response
        """

    @property
    def timezone(self):
        u"""
        Returns timezone information

        :return: Timezone information
        :rtype: dict
        :raises SmartDeviceException: on error
        """
        return self._query_helper(u"time", u"get_timezone")

    @property
    def hw_info(self):
        u"""
        Returns information about hardware

        :return: Information about hardware
        :rtype: dict
        """
        keys = [u"sw_ver", u"hw_ver", u"mac", u"mic_mac", u"type",
                u"mic_type", u"hwId", u"fwId", u"oemId", u"dev_name"]
        info = self.sys_info
        return dict((key, info[key]) for key in keys if key in info)

    @property
    def location(self):
        u"""
        Location of the device, as read from sysinfo

        :return: latitude and longitude
        :rtype: dict
        """
        info = self.sys_info
        loc = {u"latitude": None,
               u"longitude": None}

        if u"latitude" in info and u"longitude" in info:
            loc[u"latitude"] = info[u"latitude"]
            loc[u"longitude"] = info[u"longitude"]
        elif u"latitude_i" in info and u"longitude_i" in info:
            loc[u"latitude"] = info[u"latitude_i"]
            loc[u"longitude"] = info[u"longitude_i"]
        else:
            _LOGGER.warning(u"Unsupported device location.")

        return loc

    @property
    def rssi(self):
        u"""
        Returns WiFi signal strenth (rssi)

        :return: rssi
        :rtype: int
        """
        if u"rssi" in self.sys_info:
            return int(self.sys_info[u"rssi"])
        return None

    @property
    def mac(self):
        u"""
        Returns mac address

        :return: mac address in hexadecimal with colons, e.g. 01:23:45:67:89:ab
        :rtype: str
        """
        info = self.sys_info

        if u'mac' in info:
            return unicode(info[u"mac"])
        elif u'mic_mac' in info:
            return unicode(info[u'mic_mac'])
        else:
            raise SmartDeviceException(u"Unknown mac, please submit a bug"
                                       u"with sysinfo output.")

    @mac.setter
    def mac(self, mac):
        u"""
        Sets new mac address

        :param str mac: mac in hexadecimal with colons, e.g. 01:23:45:67:89:ab
        :raises SmartDeviceException: on error
        """
        self._query_helper(u"system", u"set_mac_addr", {u"mac": mac})

    def get_emeter_realtime(self):
        u"""
        Retrive current energy readings from device.

        :returns: current readings or False
        :rtype: dict, None
                  None if device has no energy meter or error occured
        :raises SmartDeviceException: on error
        """
        if not self.has_emeter:
            return None

        return self._query_helper(self.emeter_type, u"get_realtime")

    def get_emeter_daily(self,
                         year=None,
                         month=None):
        u"""
        Retrieve daily statistics for a given month

        :param year: year for which to retrieve statistics (default: this year)
        :param month: month for which to retrieve statistcs (default: this
                      month)
        :return: mapping of day of month to value
                 None if device has no energy meter or error occured
        :rtype: dict
        :raises SmartDeviceException: on error
        """
        if not self.has_emeter:
            return None

        if year is None:
            year = datetime.datetime.now().year
        if month is None:
            month = datetime.datetime.now().month

        response = self._query_helper(self.emeter_type, u"get_daystat",
                                      {u'month': month, u'year': year})

        if self.emeter_units:
            key = u'energy_wh'
        else:
            key = u'energy'

        return dict((entry[u'day'], entry[key])
                    for entry in response[u'day_list'])

    def get_emeter_monthly(self, year=None):
        u"""
        Retrieve monthly statistics for a given year.

        :param year: year for which to retrieve statistics (default: this year)
        :return: dict: mapping of month to value
                 None if device has no energy meter
        :rtype: dict
        :raises SmartDeviceException: on error
        """
        if not self.has_emeter:
            return None

        if year is None:
            year = datetime.datetime.now().year

        response = self._query_helper(self.emeter_type, u"get_monthstat",
                                      {u'year': year})

        if self.emeter_units:
            key = u'energy_wh'
        else:
            key = u'energy'

        return dict((entry[u'month'], entry[key])
                    for entry in response[u'month_list'])

    def erase_emeter_stats(self):
        u"""
        Erase energy meter statistics

        :return: True if statistics were deleted
                 False if device has no energy meter.
        :rtype: bool
        :raises SmartDeviceException: on error
        """
        if not self.has_emeter:
            return False

        self._query_helper(self.emeter_type, u"erase_emeter_stat", None)

        # As query_helper raises exception in case of failure, we have
        # succeeded when we are this far.
        return True

    def current_consumption(self):
        u"""
        Get the current power consumption in Watt.

        :return: the current power consumption in Watt.
                 None if device has no energy meter.
        :raises SmartDeviceException: on error
        """
        if not self.has_emeter:
            return None

        response = self.get_emeter_realtime()
        if self.emeter_units:
            return float(response[u'power_mw'])
        else:
            return float(response[u'power'])

    def turn_off(self):
        u"""
        Turns the device off.
        """
        raise NotImplementedError(u"Device subclass needs to implement this.")


    def toggle(self):
        if self.is_off:
            self.turn_on()
        else:
            self.turn_off()

    @property
    def is_off(self):
        u"""
        Returns whether device is off.

        :return: True if device is off, False otherwise.
        :rtype: bool
        """
        return not self.is_on

    def turn_on(self):
        u"""
        Turns the device on.
        """
        raise NotImplementedError(u"Device subclass needs to implement this.")

    @property
    def is_on(self):
        u"""
        Returns whether the device is on.

        :return: True if the device is on, False otherwise.
        :rtype: bool
        :return:
        """
        raise NotImplementedError(u"Device subclass needs to implement this.")

    @property
    def state_information(self):
        u"""
        Returns device-type specific, end-user friendly state information.
        :return: dict with state information.
        :rtype: dict
        """
        raise NotImplementedError(u"Device subclass needs to implement this.")

    def __repr__(self):
        return u"<%s at %s (%s), is_on: %s - dev specific: %s>" % (
            self.__class__.__name__,
            self.ip_address,
            self.alias,
            self.is_on,
            self.state_information)
