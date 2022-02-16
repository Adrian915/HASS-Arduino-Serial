# HASS-Arduino-Serial
Home Assistent custom component that enables Serial communication with an Arduino. Supports switches, sensors (digital / analogue read, DHT) and alarms.

Communication is done via [pySerialTransfer](https://github.com/PowerBroker2/pySerialTransfer) so you will need it set up on your system.

    pip3 install pySerialTransfer

You will also need installed in your Arduino IDE the followint, else the sketch won't compile:
1. [ArduinoSTL](https://www.arduino.cc/reference/en/libraries/arduinostl/)
2. [SerialTransfer](https://www.arduino.cc/reference/en/libraries/serialtransfer/)

Steps to get it working:
1. Set it up in the main configuration file
2. Set up sensors, switches, etc
3. Compile and the ArduinoSerialSketch library on your board. Make sure you have the libraries above first.
4. Connect your devices onto the Arduino pins
5. Plug your arduino into the USB
6. Reboot hass or the system

Sensors
---------------------
It can read three types of data: Digital, Analogue and DHT temperature / humidity values. I added the latter because I wanted the Arduino board to handle the data collection and processing of values.

Switches
---------------------
Typical Relays - nothing more to be said. I used the LED (pin 13) as a quick example.


Things to look out for
---------------------
If you're on linux remember that you need to add your user to the dialout group. The link becomes unstable if you disconnect the board and thus the component will be returning errors. A system reboot after connecting the board fixes it. (I believe it's because the component keeps the link active even after the board has been disconnected. An event to close the link is probably needed in the future).

    sudo adduser second_user dialout


Have a good one!
