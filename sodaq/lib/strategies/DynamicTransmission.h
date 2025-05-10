#ifndef DYNAMIC_TRANSMISSION_H
#define DYNAMIC_TRANSMISSION_H

#include "TransmissionStrategy.h"

class DynamicTransmission : public TransmissionStrategy
{
private:

public:
  DynamicTransmission(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t));
  virtual bool sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count) override;
};

#endif