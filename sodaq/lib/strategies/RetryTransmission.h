#ifndef RETRY_TRANSMISSION_H
#define RETRY_TRANSMISSION_H

#include "TransmissionStrategy.h"

class RetryTransmission : public TransmissionStrategy {
  private:
    void configureTransmission(uint8_t sf, uint8_t frq, uint8_t fsb);
    uint8_t _maxRetries;

  public:
    RetryTransmission(Stream* console, Sodaq_RN2483* loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t), uint8_t maxRetries = 3);
    virtual bool sendMessage(uint8_t port, uint8_t* buffer, uint8_t size, uint8_t& count) override;
};

#endif