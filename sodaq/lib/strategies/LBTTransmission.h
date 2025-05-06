#ifndef LBT_TRANSMISSION_H
#define LBT_TRANSMISSION_H

#include <Arduino.h>
#include "TransmissionStrategy.h"

// Default configuration parameters
#define DEFAULT_LORA_CHANNEL 0
#define DEFAULT_DUMMY_PAYLOAD_SIZE 4
#define DEFAULT_LISTEN_TIMEOUT 200
#define DEFAULT_RSSI_THRESHOLD -90
#define DEFAULT_MAX_RETRY_COUNT 5

// Jamming detection statistics structure
struct JammingStats {
  unsigned long totalTransmissions;
  unsigned long jammingDetected;
  unsigned long lastJammingTime;
  byte currentChannel;
  byte retryCount;
};

class LBTTransmission : public TransmissionStrategy {
  public:
    LBTTransmission(Stream* console, Sodaq_RN2483* loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t));
    
    // Configuration methods
    void setRSSIThreshold(int16_t threshold);
    void setListenTimeout(uint16_t timeout);
    void setMaxRetryCount(byte count);
    void setDummyPayloadSize(byte size);
    
    // Core functionality
    bool detectJamming();
    virtual bool sendMessage(uint8_t port, uint8_t* buffer, uint8_t size, uint8_t& count) override;
    
    // Statistics and logging
    void logJammingEvent();
    JammingStats getJammingStats();
    void resetJammingStats();
    
  private:
    // Configuration parameters
    int16_t _rssiThreshold;
    uint16_t _listenTimeout;
    byte _maxRetryCount;
    byte _dummyPayloadSize;
    
    // Jamming statistics
    JammingStats _jammingStats;
    
    // Internal helpers
    void implementMitigationStrategy();
};

#endif