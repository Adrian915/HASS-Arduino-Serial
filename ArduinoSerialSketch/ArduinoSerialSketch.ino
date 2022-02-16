#include "SharedDefs.h"
#include "SerialTransfer.h"
#include "DHTList.h"

#define CMD_RESET  0
#define CMD_DIGITAL_WRITE  1
#define CMD_DIGITAL_READ   2
#define CMD_ANALOG_WRITE   3
#define CMD_ANALOG_READ    4
#define CMD_SET_PINMODE    5
#define CMD_READ_DHT       6
#define CMD_SET_ALARM      7

SerialTransfer myTransfer;
DHTList* DHTSensors;

struct STRUCT {
  uint32_t cmd;
  uint32_t pinnum;
  double newvalue;
} dataStruct;

struct RESULT {
  uint32_t cmd;
  double data1;
  double data2;
  uint32_t result;
} resultStruct;

void setup()
{
  Serial.begin(115200);
  myTransfer.begin(Serial);

  // reet pin 13
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  DHTSensors = new DHTList();

  /*if (DEBUG_MODE)
  {
     mySerial.begin(9600);
     mySerial.println("Ready!");
  }*/
  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
}

void(* resetFunc) (void) = 0; //declare reset function @ address 0

void loop()
{
  if(myTransfer.available())
  {
    // send all received data back to Python
    // use this variable to keep track of how many
    // bytes we've processed from the receive buffer
    uint16_t recSize = 0;
    recSize = myTransfer.rxObj(dataStruct);

    uint32_t cmd = dataStruct.cmd;
    uint32_t pinnum = dataStruct.pinnum;
    double newvalue = dataStruct.newvalue;

    resultStruct.cmd = cmd;
    bool needsResult = false;

    switch(cmd)
    {
      case CMD_RESET:
      {
          resetFunc();  //call reset
          break;
      }
      case CMD_DIGITAL_WRITE:
      {
          pinMode(pinnum,OUTPUT);
          digitalWrite(pinnum,(!newvalue) ? LOW : HIGH);
          break;
      }
      case CMD_DIGITAL_READ:
      {
            needsResult = true;

            resultStruct.data1 = digitalRead(pinnum);
            resultStruct.result = 1;
            break;
      }
      case CMD_ANALOG_WRITE:
      {
        pinMode(pinnum,OUTPUT);
        analogWrite(pinnum, newvalue);
        break;
      }
      case CMD_ANALOG_READ:
      {
            needsResult = true;

            resultStruct.data1 = analogRead(pinnum);
            resultStruct.result = 1;
            break;
      }
      case CMD_READ_DHT:
      {
            needsResult = true;
            
            //populate the send buffer
            DHTWrapper* sensor = DHTSensors->GetDHTWrapper(pinnum);
            if (sensor)
            {
                resultStruct.data1 = sensor->GetTemperature();
                resultStruct.data2 = sensor->GetHumidity();
                resultStruct.result = 1;
            }
            else 
            {
                // Failed to read from DHT sensor
                resultStruct.result = 0;
                return;
            }
            break;
        }
     }

    if (needsResult)
    {
        // use this variable to keep track of how many
        // bytes we're stuffing in the transmit buffer
        uint16_t sendSize = 0;
      
        ///////////////////////////////////////// Stuff buffer with struct
        sendSize = myTransfer.txObj(resultStruct, sendSize);
      
        ///////////////////////////////////////// Send buffer
        myTransfer.sendData(sendSize);
    }
  }

  unsigned long currentMillis = millis();

  Update(currentMillis);
 }

 void Update(unsigned long currentMillis)
{

    // update DHT sensors
    if (DHTSensors)
    {
        DHTSensors->Update(currentMillis);
    }
}
