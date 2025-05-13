#ifndef STANDARD_H
#define STANDARD_H

#include "../BaseStrategy.h"

class Standard : public BaseStrategy
{
private:
public:
  Standard(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t));
  virtual bool sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count) override;
};

#endif