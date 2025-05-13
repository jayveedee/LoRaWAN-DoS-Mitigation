#ifndef RETRY_H
#define RETRY_H

#include "../BaseStrategy.h"

class Retry : public BaseStrategy
{
private:
  uint8_t _maxRetries;

public:
  Retry(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t), uint8_t maxRetries = 3);
  virtual bool sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count) override;
};

#endif