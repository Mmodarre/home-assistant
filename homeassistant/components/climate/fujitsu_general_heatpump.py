"""
Support for the Fujitsu General Split A/C.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.fujistsu/
"""

import logging
import re

import voluptuous as vol

from homeassistant.components.climate import (
    ATTR_MAX_TEMP, ATTR_MIN_TEMP, ATTR_FAN_MODE, ATTR_OPERATION_MODE,
    ATTR_SWING_MODE, ATTR_SWING_LIST, PLATFORM_SCHEMA, STATE_AUTO, STATE_COOL, STATE_DRY,
    STATE_FAN_ONLY, ATTR_FAN_LIST, STATE_HEAT, STATE_OFF, SUPPORT_FAN_MODE,
    SUPPORT_OPERATION_MODE, SUPPORT_SWING_MODE, SUPPORT_TARGET_TEMPERATURE, SUPPORT_ON_OFF,
    ClimateDevice, SUPPORT_TARGET_TEMPERATURE_HIGH, SUPPORT_TARGET_TEMPERATURE_LOW)

from homeassistant.const import (ATTR_TEMPERATURE, CONF_USERNAME, CONF_PASSWORD, TEMP_CELSIUS) 
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pyfujitsu==0.7.1.3']

_LOGGER = logging.getLogger(__name__)
SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
})

HA_STATE_TO_FUJITSU = {
    STATE_FAN_ONLY: 'FAN',
    STATE_DRY: 'DRY',
    STATE_COOL: 'COOL',
    STATE_HEAT: 'HEAR',
    STATE_AUTO: 'AUTO',
    STATE_OFF: 'OFF',
}


FUJITSU_TO_HA_STATE = {
    'FAN': STATE_FAN_ONLY,
    'DRY': STATE_DRY,
    'COOL': STATE_COOL,
    'HEAT': STATE_HEAT,
    'AUTO': STATE_AUTO,
    'OFF': STATE_OFF,
}

HA_ATTR_TO_FUJITSU = {
    ATTR_OPERATION_MODE: 'operation_mode',
    ATTR_FAN_MODE: 'fan_speed',
    ## Needs a swing mode attr to cover both horizontal and vertical in splitAC.py
    ATTR_SWING_MODE: 'af_vertical_swing',
    #ATTR_TARGET_TEMPERATURE: 'adjust_temperature',
    # TO DO
    ATTR_SWING_LIST : ''
}

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Fujitsu Split platform."""
    #import homeassistant.components.pyfujitsu.api as fgapi
    import pyfujitsu.api as fgapi
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    _LOGGER.debug("Added Fujitsu Account for username: %s ", username)

    fglairapi = fgapi.Api(username, password)
    if not fglairapi._authenticate():
        _LOGGER.error("Unable to authenticate with Fujistsu General")
        return
    ##TODO get devices shoud return DSNs
    add_devices(FujitsuClimate(fglairapi, dsn) for dsn in fglairapi._get_devices())

class FujitsuClimate(ClimateDevice):
    """Representation of a Fujitsu HVAC."""

    def __init__(self, api, dsn):
        #from homeassistant.components.pyfujitsu import splitAC
        from pyfujitsu import splitAC
        
        self._api = api
        self._dsn = dsn
        self._fujitsu_device = splitAC.splitAC(self._api, self._dsn)
        self._name = self._fujitsu_device.device_name
        #Todo make this dynamic
        #self._supported_features = SUPPORT_TARGET_TEMPERATURE \
        #    | SUPPORT_OPERATION_MODE | SUPPORT_FAN_MODE  \
        #    | SUPPORT_OPERATION_MODE
        self._support_flags = SUPPORT_FLAGS
        if self.target_temperature is not None:
            self._support_flags = self._support_flags | SUPPORT_TARGET_TEMPERATURE
        if self.current_fan_mode is not None:
            self._support_flags = self._support_flags | SUPPORT_FAN_MODE
        if self.current_swing_mode is not None:
            self._support_flags = self._support_flags | SUPPORT_SWING_MODE
        if self.current_operation is not None:
            self._support_flags = self._support_flags | SUPPORT_OPERATION_MODE
        if self.target_temperature_high is not None:
            self._support_flags = \
                self._support_flags | SUPPORT_TARGET_TEMPERATURE_HIGH
        if self.target_temperature_low is not None:
            self._support_flags = \
                self._support_flags | SUPPORT_TARGET_TEMPERATURE_LOW
        if self.is_on is not None:
            self._support_flags = self._support_flags | SUPPORT_ON_OFF
        self._target_temperature = self.target_temperature
        self._target_humidity = self.target_humidity
        self._unit_of_measurement = self.unit_of_measurement
        self._current_fan_mode = self.current_fan_mode
        self._current_operation = self.current_operation
        self._current_swing_mode = self.current_swing_mode
        self._fan_list = ['Quiet', 'Low', 'Medium', 'High', 'Auto']
        self._operation_list = ['Heat', 'Cool', 'Auto', 'Dry', 'Fan' , 'Off']
        self._swing_list = ['Vertical Swing','Horizontal Swing', 'Vertical high', 'Vertical Mid', 'Vertical Low' ]
        self._target_temperature_high = self.target_temperature_high
        self._target_temperature_low = self.target_temperature_low
        self._on = self.is_on
        


    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS


    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._fujitsu_device.operation_mode_desc

    @property
    #### todo in splitAC to return a list of all possible operation modes
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._fujitsu_device.adjust_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 0.5

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return 30

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        return 16

    @property
    def is_on(self):
        """Return true if on."""
        if self._fujitsu_device.operation_mode != 0:
            return True
        else:
            return False

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        return self._fujitsu_device.operation_mode.fan_speed

    @property
    ## Todo!!
    def fan_list(self):
        """Return the list of available fan modes."""
        return self._fan_list

    @property
    ## Todo combine swing modes in to one
    def current_swing_mode(self):
        """Return the fan setting."""
        return self._fujitsu_device.operation_mode.af_horizontal_direction

    @property
    ## Todo!
    def swing_list(self):
        """Return the list of available swing modes."""
        return self._swing_list

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        self._fujitsu_device.adjust_temperature(kwargs)

## up to here!
    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self._fujitsu_device.fan_speed = fan_mode

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        self._fujitsu_device.change_operation_mode(operation_mode)

#    def set_swing_mode(self, swing_mode):
#        """Set new target swing operation."""
#        raise NotImplementedError()


    def turn_on(self):
        """Turn device on."""
        return self._fujitsu_device.turnOn()


    def turn_off(self):
        """Turn device off."""
        return self._fujitsu_device.turnOff()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._su