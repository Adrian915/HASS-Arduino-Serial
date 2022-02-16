"""
Support for Arduino boards running with the Firmata firmware.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/arduino/
"""
import logging
import struct
import pySerialTransfer
import time
import voluptuous as vol

from pySerialTransfer import pySerialTransfer as txfer
from homeassistant.const import (
    EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP)
from homeassistant.const import CONF_PORT
import homeassistant.helpers.config_validation as cv

CMD_RESET = 0
CMD_DIGITAL_WRITE = 1
CMD_DIGITAL_READ  = 2
CMD_ANALOG_WRITE  = 3
CMD_ANALOG_READ   = 4
CMD_SET_PINMODE   = 5
CMD_READ_DHT      = 6
CMD_ALARM_AUDIO   = 7

CONF_SERIAL_PORT = 'port'
CONF_SERIAL_BAUDRATE = 'baudrate'

CONF_PORTS = 'ports'

REQUIREMENTS = ['pySerialTransfer']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ArduinoSerial'

PORT_SCHEMA = vol.Schema({
    vol.Optional(CONF_SERIAL_BAUDRATE, default=115200): cv.positive_int,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_PORTS, default={}):
            vol.Schema({cv.string: PORT_SCHEMA}),
    }),
}, extra=vol.ALLOW_EXTRA)

class struct(object):
    cmd = 0
    pinnum = 0
    newvalue = 1.0
    def __init__(self, cmd, pinnum, newvalue):
        self.cmd = int(cmd)
        self.pinnum = int(pinnum)
        self.newvalue = float(newvalue)

class result(object):
    cmd = 0
    data1 = 0
    data2 = 0
    result = 0
    def __init__(self, cmd, data1, data2, result):
        self.cmd = int(cmd)
        self.data1 = float(data1)
        self.data2 = float(data2)
        self.result = int(result)


def setup(hass, config):
    """Set up the SERIAL component."""
    global _Ports
    _Ports = []
    
    #set up my ports
    ports = config[DOMAIN][CONF_PORTS]
    
    for port, baudratecoll in ports.items():
        baudRateVal = baudratecoll['baudrate']
        _LOGGER.info("Opening serial port %s with baudrate %s", port, baudRateVal )
        _Ports.append(SerialBoard(port, baudRateVal))

    def stop_ardSerial(event):
        """Stop the serial service."""
        for port in _Ports:
           port.disconnect();

    def start_ardSerial(event):
        """Start the Arduino service."""
        hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, stop_ardSerial)

    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, start_ardSerial)

    return True


class SerialBoard(object):
    """Representation of an Arduino board."""
    def __init__(self, portName, baudRate):
        """Initialize the board."""
        self.port = portName
        self.baudRate = baudRate
        self._isBusy = False
        try:
            self.link = txfer.SerialTransfer(portName)
            self.link.open()
            
            # send a reset to the board, just because
            self.reset()
        except BaseException as e:
          _LOGGER.error("Could not open serial port %s", portName, str(e))
        
    def get_float(self, data, index, offset = 0):
        bts = data[offset+(4*index):offset+((index+1)*4)]
        res = struct.unpack("f", bytes(bts))[0]
        return round(res, 2)
  
    def get_digital(self, pin):
        """ get the value of a digital pin """
        # send the command that we want to execute   
        return self.perform_cmd(CMD_DIGITAL_READ, pin, 0)
        
    def get_readdht(self, pin):
        # send the command that we want to execute   
        return self.perform_cmd(CMD_READ_DHT, pin, 0)
        
    def get_analogue(self, pin):
        """ get the value of aan analogue pin """
        # send the command that we want to execute   
        return self.perform_cmd(CMD_ANALOG_READ, pin, 0)
        
    def perform_cmd(self, cmd, pin, newPinValue):
        results = [0, 0]     
        # board is busy, try again later
        if (self._isBusy):
            _LOGGER.warning("Port %s is busy, postponing command %i on %i", self.port, cmd, pin)
            # give some time to finish the execution of the current command
            time.sleep(0.50)
            return self.perform_cmd(port, cmd, pin, newPinValue)
        
        # lock board as busy
        self._isBusy = True
        serialFail = False
        
        # send the command that we want to execute   
        try:
           newPackage = struct(cmd,pin,newPinValue)
           sendSize = 0
            
           sendSize = self.link.tx_obj(newPackage.cmd, start_pos=sendSize)
           sendSize = self.link.tx_obj(newPackage.pinnum, start_pos=sendSize)
           sendSize = self.link.tx_obj(newPackage.newvalue, start_pos=sendSize)
         
           self.link.send(sendSize)
           
        except BaseException as e:
           serialFail = True
           _LOGGER.error("Exception occurred when writing serial command", str(e))
        
        self._isBusy = False
         
        needsResponse = (cmd != CMD_DIGITAL_WRITE and cmd != CMD_ALARM_AUDIO)

        # request response if we need it and writing was not a faliure
        if (serialFail == False and needsResponse):
            try:
                # get response
                recPackage = result(0,0,0,0)
                recSize = 0
                      
                ###################################################################
                # Wait for a response and report any errors while receiving packets
                ###################################################################
                while not self.link.available():
                    if self.link.status < 0:
                        if self.link.status == txfer.CRC_ERROR:
                            _LOGGER.error("ERROR: CRC_ERROR")
                            break
                        elif self.link.status == txfer.PAYLOAD_ERROR:
                            _LOGGER.error("ERROR: PAYLOAD_ERROR")
                            break
                        elif self.link.status == txfer.STOP_BYTE_ERROR:
                            _LOGGER.error("ERROR: STOP_BYTE_ERROR")
                            break
                        else:
                            _LOGGER.error('ERROR: {}'.format(self.link.status))
                            break
                        

                recPackage.cmd = self.link.rx_obj(obj_type='i', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['i']
                
                recPackage.data1 = self.link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']
                
                recPackage.data2 = self.link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']
                
                recPackage.result = self.link.rx_obj(obj_type='i', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['i']

                if ( recPackage.cmd != cmd or recPackage.result == 0):
                    _LOGGER.error("Incorrect return package for command %i on pin %i: %s",cmd, pin)
                else:
                    # data was good
                    results[0] = "{:.2f}".format(recPackage.data1)
                    results[1] = "{:.2f}".format(recPackage.data2)
            except BaseException as e:
               _LOGGER.error("Unable to parse results for command %i on pin %i: %s",cmd, pin, str(e))
        
        return results

    def set_digital_high(self, pin):
        """Set a given digital pin to high."""
        self.perform_cmd(CMD_DIGITAL_WRITE, pin, 1)

    def set_digital_low(self, pin):
        """Set a given digital pin to low."""
        self.perform_cmd(CMD_DIGITAL_WRITE, pin, 0)
    
    def reset(self):
        # send the command that we want to execute   
        return self.perform_cmd(CMD_RESET)
        
    def disconnect(self):
        """Disconnect the board and close the serial connection."""
        self.link.close()
