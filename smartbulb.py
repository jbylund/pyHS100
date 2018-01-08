from __future__ import division
from __future__ import absolute_import
from tplink import SmartDevice
from typing import Any, Dict, Optional, Tuple


class SmartBulb(SmartDevice):
    u"""Representation of a TP-Link Smart Bulb.

    Usage example when used as library:
    p = SmartBulb("192.168.1.105")
    # print the devices alias
    print(p.alias)
    # change state of bulb
    p.state = "ON"
    p.state = "OFF"
    # query and print current state of plug
    print(p.state)
    # check whether the bulb supports color changes
    if p.is_color:
    # set the color to an HSV tuple
    p.hsv = (180, 100, 100)
    # get the current HSV value
    print(p.hsv)
    # check whether the bulb supports setting color temperature
    if p.is_variable_color_temp:
    # set the color temperature in Kelvin
    p.color_temp = 3000
    # get the current color temperature
    print(p.color_temp)
    # check whether the bulb is dimmable
    if p.is_dimmable:
    # set the bulb to 50% brightness
    p.brightness = 50
    # check the current brightness
    print(p.brightness)

    Errors reported by the device are raised as SmartDeviceExceptions,
    and should be handled by the user of the library.

    """
    # bulb states
    BULB_STATE_ON = u'ON'
    BULB_STATE_OFF = u'OFF'

    def __init__(self,
                 ip_address,
                 protocol=None):
        SmartDevice.__init__(self, ip_address, protocol)
        self.emeter_type = u"smartlife.iot.common.emeter"
        self.emeter_units = True

    @property
    def is_color(self):
        u"""
        Whether the bulb supports color changes

        :return: True if the bulb supports color changes, False otherwise
        :rtype: bool
        """
        return bool(self.sys_info[u'is_color'])

    @property
    def is_dimmable(self):
        u"""
        Whether the bulb supports brightness changes

        :return: True if the bulb supports brightness changes, False otherwise
        :rtype: bool
        """
        return bool(self.sys_info[u'is_dimmable'])

    @property
    def is_variable_color_temp(self):
        u"""
        Whether the bulb supports color temperature changes

        :return: True if the bulb supports color temperature changes, False
        otherwise
        :rtype: bool
        """
        return bool(self.sys_info[u'is_variable_color_temp'])

    def get_light_state(self):
        return self._query_helper(u"smartlife.iot.smartbulb.lightingservice",
                                  u"get_light_state")

    def set_light_state(self, state):
        return self._query_helper(u"smartlife.iot.smartbulb.lightingservice",
                                  u"transition_light_state", state)

    @property
    def hsv(self):
        u"""
        Returns the current HSV state of the bulb, if supported

        :return: hue, saturation and value (degrees, %, %)
        :rtype: tuple
        """

        if not self.is_color:
            return None

        light_state = self.get_light_state()
        if not self.is_on:
            hue = light_state[u'dft_on_state'][u'hue']
            saturation = light_state[u'dft_on_state'][u'saturation']
            value = int(light_state[u'dft_on_state']
                        [u'brightness'] * 255 / 100)
        else:
            hue = light_state[u'hue']
            saturation = light_state[u'saturation']
            value = int(light_state[u'brightness'] * 255 / 100)

        return hue, saturation, value

    @hsv.setter
    def hsv(self, state):
        u"""
        Sets new HSV, if supported

        :param tuple state: hue, saturation and value (degrees, %, %)
        """
        if not self.is_color:
            return None

        light_state = {
            u"hue": state[0],
            u"saturation": state[1],
            u"brightness": int(state[2] * 100 / 255),
            u"color_temp": 0
        }
        self.set_light_state(light_state)

    @property
    def color_temp(self):
        u"""
        Color temperature of the device, if supported

        :return: Color temperature in Kelvin
        :rtype: int
        """
        if not self.is_variable_color_temp:
            return None

        light_state = self.get_light_state()
        if not self.is_on:
            return int(light_state[u'dft_on_state'][u'color_temp'])
        else:
            return int(light_state[u'color_temp'])

    @color_temp.setter
    def color_temp(self, temp):
        u"""
        Set the color temperature of the device, if supported

        :param int temp: The new color temperature, in Kelvin
        """
        if not self.is_variable_color_temp:
            return None

        light_state = {
            u"color_temp": temp,
        }
        self.set_light_state(light_state)

    @property
    def brightness(self):
        u"""
        Current brightness of the device, if supported

        :return: brightness in percent
        :rtype: int
        """
        if not self.is_dimmable:
            return None

        light_state = self.get_light_state()
        if not self.is_on:
            return int(light_state[u'dft_on_state'][u'brightness'])
        else:
            return int(light_state[u'brightness'])

    @brightness.setter
    def brightness(self, brightness):
        u"""
        Set the current brightness of the device, if supported

        :param int brightness: brightness in percent
        """
        if not self.is_dimmable:
            return None

        light_state = {
            u"brightness": brightness,
        }
        self.set_light_state(light_state)

    @property
    def state(self):
        u"""
        Retrieve the bulb state

        :returns: one of
                  BULB_STATE_ON
                  BULB_STATE_OFF
        :rtype: str
        """
        light_state = self.get_light_state()
        if light_state[u'on_off']:
            return self.BULB_STATE_ON
        return self.BULB_STATE_OFF

    @state.setter
    def state(self, bulb_state):
        u"""
        Set the new bulb state

        :param bulb_state: one of
                           BULB_STATE_ON
                           BULB_STATE_OFF
        """
        if bulb_state == self.BULB_STATE_ON:
            new_state = 1
        elif bulb_state == self.BULB_STATE_OFF:
            new_state = 0
        else:
            raise ValueError

        light_state = {
            u"on_off": new_state,
        }
        self.set_light_state(light_state)

    @property
    def state_information(self):
        u"""
        Return bulb-specific state information.
        :return: Bulb information dict, keys in user-presentable form.
        :rtype: dict
        """
        info = {
            u'Brightness': self.brightness,
            u'Is dimmable': self.is_dimmable,
        }  # type: Dict[str, Any]
        if self.is_variable_color_temp:
            info[u"Color temperature"] = self.color_temp
        if self.is_color:
            info[u"HSV"] = self.hsv

        return info

    @property
    def is_on(self):
        return bool(self.state == self.BULB_STATE_ON)

    def turn_off(self):
        u"""
        Turn the bulb off.
        """
        self.state = self.BULB_STATE_OFF

    def turn_on(self):
        u"""
        Turn the bulb on.
        """
        self.state = self.BULB_STATE_ON

    @property
    def has_emeter(self):
        return True
