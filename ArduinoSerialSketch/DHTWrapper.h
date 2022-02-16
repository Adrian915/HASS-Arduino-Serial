#ifndef DHTWrapper_h
#define DHTWrapper_h

#include "SharedDefs.h"
#include "DHT.h"

// keep it alive for half an hour
#define LIVE_TIME 600000
// update every 3 seconds
#define UPDATE_INTERVAL 3000

#define MAX_FALIURES 6
class DHTWrapper : public dht
{
private:
	uint8_t Pin;
	bool markedForDeletion = false;
	bool isAlarm = false;
	
	double ValidHumidity;
	double ValidTemperature;
	
	long thinkLast = 0;        			 // will store last think time
	int faliureCount = 0;

  bool wasNeeded = true;
	volatile unsigned long LastMillisNeeded;
        
public:
    DHTWrapper(int pinNum);
	
	uint8_t GetPin() {return Pin; };
	
	virtual float GetTemperature();
	virtual float GetHumidity();
	
    virtual void Update(unsigned long currentMillis);
	
	bool IsAlarm() { return isAlarm; };
        
	//deletion
	bool ShouldDelete() { return markedForDeletion; }
	void SetShouldDelete(bool b) { markedForDeletion = b; }
};

#endif
