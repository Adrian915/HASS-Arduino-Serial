"""
Support for HTU21D temperature and humidity sensor.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.htu21d/
"""
import logging
import math

import voluptuous as vol
from datetime import timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    PERCENTAGE,
    TIME_HOURS,
    CONF_NAME, 
    ATTR_FRIENDLY_NAME,
    CONF_MONITORED_CONDITIONS)
import custom_components.ArduinoSerial as ArduinoSerial

_LOGGER = logging.getLogger(__name__)


MAX_UPDATE_FALIURES = 4

CONF_PORTS = 'ports'
CONF_PINS = 'pins'
CONF_UNIQUE_ID = 'unique_id'
CONF_ICON = 'icon'

SENSOR_TEMPERATURE = 'temperature'
SENSOR_HUMIDITY = 'humidity'
SENSOR_ANALOGUE_VALUE = 'analogue_value'

SENSOR_TYPES = {
    SENSOR_TEMPERATURE: ['Temperature', TEMP_CELSIUS, "mdi:thermometer"],
    SENSOR_HUMIDITY: ["Humidity", PERCENTAGE, "mdi:water-percent"],
    SENSOR_ANALOGUE_VALUE: ['Percentage', PERCENTAGE, "mdi:theme-light-dark"],
}
DEFAULT_NAME = 'Arduino Serial Sensor'

# DHT11 is able to deliver data once per second, DHT22 once every two
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=3)

PIN_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_MONITORED_CONDITIONS, default=[]):
       vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
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
    """Set up the sensor."""
    
 # Verify that we have ports set up
    if ArduinoSerial._Ports is None:
        _LOGGER.error("There are no available arduino serial ports")
        return False

    #set up my sensors
    ports = config.get(CONF_PORTS)
    
    devices = []
    for portName, pinList in ports.items():
        serialBoard = next((inst for inst in ArduinoSerial._Ports if inst.port == portName), None)
        if (serialBoard is not None):
            for pins, pinData in pinList.items():
               for pinID, deviceData in pinData.items():
                  _LOGGER.info("Setting up switch on pin %i with options %s, using board %s", pinID, deviceData, deviceData)
                  monitored_conditions = deviceData.get(CONF_MONITORED_CONDITIONS)
                  try:
                    for sensorType in monitored_conditions:
                        devices.append(ArduinoSerialSensor(pinID, serialBoard, sensorType, deviceData))
                  except KeyError:
                    continue
        else:
          _LOGGER.error("No arduino serial board named %s was found", portName)

    add_devices(devices)
    
    return True


class ArduinoSerialSensor(Entity):
    """Representation of a ArduinoSerial sensor."""

    def __init__(self, pin, board, sensor_type, options):
        """Initialize the Pin."""
        self._pin = pin
        self._type = sensor_type
        self._board = board
        self.client_name = options.get(CONF_NAME)
        self._name = "%s (%s)" % (self.client_name, SENSOR_TYPES[sensor_type][0])
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._value = None
        self._fail_attempts = 0
        self._unique_id = options.get(CONF_UNIQUE_ID)

    @property
    def name(self):
        """Get the name of the pin."""
        return self._name
        
    @property
    def icon(self):
        """Icon to use in the frontend."""
        return SENSOR_TYPES[self._type][2]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._value
        
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest value from the pin."""
        if (self._board._isBusy):
            _LOGGER.warning("board is busy, skipping update of device " + self._name)
        else: 
            result = None
            
            try:
                # set the results
                if (self._type == SENSOR_ANALOGUE_VALUE):
                    result = self._board.get_analogue(self._pin)
                else:
                    result = self._board.get_readdht(self._pin)
                    
                if (result is None):
                    if (self._fail_attempts < MAX_UPDATE_FALIURES):
                        self._fail_attempts += 1
                    else:
                        self._value = float('nan')
                else:
                    self._fail_attempts = 0
                    if (self._type == SENSOR_ANALOGUE_VALUE):
                        # raw is between 0(high brightness) and 1023 (darkest)
                        pLight = (100 - ((result[0]/1023) * 100))
                        self._value = int(pLight)
                    elif (self._type == SENSOR_TEMPERATURE):
                        self._value = result[0]
                    elif (self._type == SENSOR_HUMIDITY):
                        self._value = result[1]
            except BaseException as e:
                _LOGGER.error("Could not update sensor" + self._name)
