//=========================   2014, CAR PROJECT   =============================//
// Purpose: Basic circuit
//
//=============================================================================//
#include "DHTWrapper.h"

//=============================================================================//
// CONSTRUCTOR AND DESTRUCTOR
//=============================================================================//
DHTWrapper::DHTWrapper(int pinNum) : dht()
{
	Pin = pinNum;
  wasNeeded = true;
}

//=============================================================================//
// think and other events
//=============================================================================//
void DHTWrapper::Update(unsigned long currentMillis)
{
	// not needed anymore
	if (markedForDeletion)
		return;

	if(currentMillis - thinkLast >= UPDATE_INTERVAL) 
	{
    //update
    thinkLast = currentMillis;
    
    if (wasNeeded)
    {
      LastMillisNeeded = currentMillis;
      wasNeeded = false;
    }
    else
    {
      if (currentMillis - LastMillisNeeded >= LIVE_TIME)
      {
          markedForDeletion = true;
          if (DEBUG_MODE)
          {
            Serial.println("Flagging DHT to delete");
            Serial.print(Pin);
            Serial.println();
          }
          return;
      }
    }
	
	int res = read22(Pin);
	
	switch (res)
	{
		case 0:
			ValidTemperature = temperature;
			ValidHumidity = humidity;
			
			//reset failure count
			faliureCount = 0;
			isAlarm = false;
      
			if (DEBUG_MODE)
			{
				Serial.print("updated temp: ");
				Serial.print(temperature);
				Serial.print(" | hum: ");
				Serial.print(humidity);
				Serial.println();
			}
			break;
		case -1:
		case -2:
			if (DEBUG_MODE)
			{
				Serial.println();
				Serial.print("Failed to read from DHT sensor!");
				Serial.print(Pin);
				Serial.println();
			}
			faliureCount++;
			
			if (faliureCount >= MAX_FALIURES)
			{
				isAlarm = true;
				if (DEBUG_MODE)
				{
					Serial.println();
					Serial.print("Catastrophic faliure on DHT pin");
					Serial.print(Pin);
					Serial.println();
				}
			}
			break;
	}
		
	/*	// Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
		float h = DHTInst.readHumidity();
		// Read temperature as Celsius (the default)
		float t = DHTInst.readTemperature();
		
		// Check if any reads failed and exit early (to try again).
		if (isnan(h) || isnan(t)) 
		{
      if (DEBUG_MODE)
      {
            Serial.println();
      			Serial.print("Failed to read from DHT sensor!");
            Serial.print(Pin);
            Serial.println();
      }
			faliureCount++;
			
			if (faliureCount >= MAX_FALIURES)
			{
				isAlarm = true;
        if (DEBUG_MODE)
        {
                Serial.println();
        				Serial.print("Catastrophic faliure on DHT pin");
                Serial.print(Pin);
                Serial.println();
        }
			}
		}
		else
		{	  
			// update temp
			lastTemp = t;
			
			// and humidity
			lastHum = h;

      if (DEBUG_MODE)
      {
            Serial.println();
      			Serial.print("updated temp: ");
      			Serial.print(t);
      			Serial.print(" updated hum: ");
      			Serial.print(h);
      			Serial.println();
      }
			
			//reset failure count
			faliureCount = 0;
			isAlarm = false;
		}
	}*/
}
}

float DHTWrapper::GetTemperature()
{
  wasNeeded = true;
  markedForDeletion = false;
  
  return ValidTemperature;
}

float DHTWrapper::GetHumidity()
{
  wasNeeded = true;
  markedForDeletion = false;
  
  return ValidHumidity;
}
