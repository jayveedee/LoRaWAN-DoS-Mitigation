#ifndef TRANSMISSION_STRATEGY_H
#define TRANSMISSION_STRATEGY_H

#include <Arduino.h>
#include "../Sodaq_RN2483/Sodaq_RN2483.h"

class TransmissionStrategy
{
protected:
  Stream *_console;
  Sodaq_RN2483 *_loRaBee;
  void (*_setRgbColor)(uint8_t red, uint8_t green, uint8_t blue);

  bool handleErrorState(uint8_t res, uint8_t &count);
  void configureTransmission(uint8_t sf, uint8_t frq, uint8_t fsb);

public:
  TransmissionStrategy(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t));
  virtual bool sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count) = 0;
  virtual void fetchFrameCounters();
  virtual ~TransmissionStrategy() {}
};

#endif