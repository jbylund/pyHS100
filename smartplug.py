from __future__ import absolute_import
import datetime
import logging
from typing import Any, Dict

from pyHS100 import SmartDevice

_LOGGER = logging.getLogger(__name__)


class SmartPlug(SmartDevice):
    u"""Representation of a TP-Link Smart Switch.

    Usage example when used as library:
    p = SmartPlug("192.168.1.105")
    # print the devices alias
    print(p.alias)
    # change state of plug
    p.state = "ON"
    p.state = "OFF"
    # query and print current state of plug
    print(p.state)

    Errors reported by the device are raised as SmartDeviceExceptions,
    and should be handled by the user of the library.

    Note:
    The library references the same structure as defined for the D-Link Switch
    """
    # switch states
    SWITCH_STATE_ON = u'ON'
    SWITCH_STATE_OFF = u'OFF'
    SWITCH_STATE_UNKNOWN = u'UNKNOWN'

    def __init__(self,
                 ip_address,
                 protocol=None):
        SmartDevice.__init__(self, ip_address, protocol)
        self.emeter_type = u"emeter"
        self.emeter_units = False

    @property
    def state(self):
        u"""
        Retrieve the switch state

        :returns: one of
                  SWITCH_STATE_ON
                  SWITCH_STATE_OFF
                  SWITCH_STATE_UNKNOWN
        :rtype: str
        """
        relay_state = self.sys_info[u'relay_state']

        if relay_state == 0:
            return SmartPlug.SWITCH_STATE_OFF
        elif relay_state == 1:
            return SmartPlug.SWITCH_STATE_ON
        else:
            _LOGGER.warning(u"Unknown state %s returned.", relay_state)
            return SmartPlug.SWITCH_STATE_UNKNOWN

    @state.setter
    def state(self, value):
        u"""
        Set the new switch state

        :param value: one of
                    SWITCH_STATE_ON
                    SWITCH_STATE_OFF
        :raises ValueError: on invalid state
        :raises SmartDeviceException: on error

        """
        if not isinstance(value, unicode):
            raise ValueError(u"State must be str, not of %s.", type(value))
        elif value.upper() == SmartPlug.SWITCH_STATE_ON:
            self.turn_on()
        elif value.upper() == SmartPlug.SWITCH_STATE_OFF:
            self.turn_off()
        else:
            raise ValueError(u"State %s is not valid.", value)

    @property
    def has_emeter(self):
        u"""
        Returns whether device has an energy meter.
        :return: True if energy meter is available
                 False otherwise
        """
        features = self.sys_info[u'feature'].split(u':')
        return SmartDevice.FEATURE_ENERGY_METER in features

    @property
    def is_on(self):
        u"""
        Returns whether device is on.

        :return: True if device is on, False otherwise
        """
        return bool(self.sys_info[u'relay_state'])

    def turn_on(self):
        u"""
        Turn the switch on.

        :raises SmartDeviceException: on error
        """
        self._query_helper(u"system", u"set_relay_state", {u"state": 1})

    def turn_off(self):
        u"""
        Turn the switch off.

        :raises SmartDeviceException: on error
        """
        self._query_helper(u"system", u"set_relay_state", {u"state": 0})

    @property
    def led(self):
        u"""
        Returns the state of the led.

        :return: True if led is on, False otherwise
        :rtype: bool
        """
        return bool(1 - self.sys_info[u"led_off"])

    @led.setter
    def led(self, state):
        u"""
        Sets the state of the led (night mode)

        :param bool state: True to set led on, False to set led off
        :raises SmartDeviceException: on error
        """
        self._query_helper(u"system", u"set_led_off", {u"off": int(not state)})

    @property
    def on_since(self):
        u"""
        Returns pretty-printed on-time

        :return: datetime for on since
        :rtype: datetime
        """
        return datetime.datetime.now() - \
            datetime.timedelta(seconds=self.sys_info[u"on_time"])

    @property
    def state_information(self):
        return {
            u'LED state': self.led,
            u'On since': self.on_since
        }
