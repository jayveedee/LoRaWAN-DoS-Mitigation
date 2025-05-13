#ifndef DYNAMIC_TRANSMISSION_H
#define DYNAMIC_TRANSMISSION_H

#include "TransmissionStrategy.h"

class DynamicTransmission : public TransmissionStrategy
{
protected:
  uint8_t sf = 9;
  uint8_t frq = 1;
  uint8_t fsb = 0;
  uint8_t res = 0xFF;

  bool configureDynamicTransmission(bool withRetry, uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count);

public:
  DynamicTransmission(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t));
  virtual bool sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count) override;
};

#endif