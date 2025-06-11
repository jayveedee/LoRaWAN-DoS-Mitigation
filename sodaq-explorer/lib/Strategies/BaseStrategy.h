#ifndef BASE_STRATEGY_H
#define BASE_STRATEGY_H

#include <Arduino.h>
#include "../Sodaq_RN2483/Sodaq_RN2483.h"

struct FrameCounters
{
  int downlink;
  int uplink;
};

class BaseStrategy
{
protected:
  Stream *_console;
  Stream *_loraStream;
  Sodaq_RN2483 *_loRaBee;
  void (*_setRgbColor)(uint8_t red, uint8_t green, uint8_t blue);

  bool handleErrorState(uint8_t res, uint8_t &count, int sf);
  void configureTransmission(const char *cr, uint8_t sf, uint8_t frq, uint8_t fsb);

public:
  BaseStrategy(Stream *console, Stream *loraStream, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t));
  virtual bool sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count) = 0;
  virtual FrameCounters fetchFrameCounters();
  virtual ~BaseStrategy() {}

  void printTransmissionCounters();

private:
  const int MIN_SF = 9;
  const int MAX_SF = 12;
  int transmissionCounters[4] = {0};

  void incrementTransmissionCount(int sf);
};

#endif