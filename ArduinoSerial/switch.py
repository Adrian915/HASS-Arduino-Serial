"""
Support for HTU21D temperature and humidity sensor.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.htu21d/
"""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.components.switch import (SwitchEntity, PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    CONF_NAME,
    ATTR_FRIENDLY_NAME
)

import custom_components.ArduinoSerial as ArduinoSerial

DEPENDENCIES = ['ArduinoSerial']

_LOGGER = logging.getLogger(__name__)


CONF_PORTS = 'ports'
CONF_PINS = 'pins'
CONF_NEGATE = 'negate'
CONF_INITIAL = 'initial'
CONF_UNIQUE_ID = 'unique_id'
CONF_ICON = 'icon'

DEFAULT_NAME = 'ArduinoSerial Switch'

PIN_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_INITIAL, default=False): cv.boolean,
    vol.Optional(CONF_NEGATE, default=False): cv.boolean,
    vol.Optional(ATTR_FRIENDLY_NAME): cv.string,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
    vol.Optional(CONF_ICON): cv.string,
})

PORT_SCHEMA = vol.Schema({
    vol.Required(CONF_PINS, default={}):
       vol.Schema({cv.positive_int: PIN_SCHEMA}),
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORTS, default={}):
       vol.Schema({cv.string: PORT_SCHEMA}),
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the switch."""
 
    # Verify that we have ports set up
    if ArduinoSerial._Ports is None:
        _LOGGER.error("There are no available arduino serial ports")
        return False
 
    #set up my switches
    ports = config.get(CONF_PORTS)

    switches = []
    for portName, pinList in ports.items():
        serialBoard = next((inst for inst in ArduinoSerial._Ports if inst.port == portName), None)
        if (serialBoard is not None):
            for pins, pinData in pinList.items():
               for pinID, deviceData in pinData.items():
                  switches.append(ArduinoSerialSwitch(serialBoard, pinID, deviceData))
        else:
          _LOGGER.error("No arduino serial board named %s was found", portName)

    add_devices(switches)
    return True


class ArduinoSerialSwitch(SwitchEntity):
    """Representation of a ArduinoSerial switch."""

    def __init__(self, board, pin, options):
        """Initialize the Pin."""
        self._pin = pin
        self._board = board
        self._name = options.get(CONF_NAME)
        self._state = options.get(CONF_INITIAL)
        self._negate = options.get(CONF_NEGATE)
        self._friendly_name = options.get(ATTR_FRIENDLY_NAME)
        self._unique_id = options.get(CONF_UNIQUE_ID)
        self._icon = options.get(CONF_ICON)
        
        if  self._negate:
            self.turn_on_handler = self._board.set_digital_low
            self.turn_off_handler = self._board.set_digital_high
        else:
            self.turn_on_handler = self._board.set_digital_high
            self.turn_off_handler = self._board.set_digital_low

        (self.turn_on_handler if self._state else self.turn_off_handler)(pin)

    @property
    def name(self):
        """Get the name of the pin."""
        return self._name
        
    @property
    def unique_id(self):
        """Return the unique id of this switch."""
        return self._unique_id
        
    @property
    def icon(self):
        """Icon to use in the frontend."""
        return self._icon

    @property
    def is_on(self):
        """Return true if pin is high/on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the pin to high/on."""
        self._state = True
        self.turn_on_handler(self._pin)

    def turn_off(self, **kwargs):
        """Turn the pin to low/off."""
        self._state = False
        self.turn_off_handler(self._pin)
