#include "BaseStrategy.h"

BaseStrategy::BaseStrategy(Stream *console, Stream *loraStream, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
{
  _console = console;
  _loraStream = loraStream;
  _loRaBee = loRaBee;
  _setRgbColor = setRgbColorCallback;
}

void BaseStrategy::incrementTransmissionCount(int sf)
{
  if (sf >= MIN_SF && sf <= MAX_SF)
  {
    transmissionCounters[sf - MIN_SF]++;
  }
}

void BaseStrategy::printTransmissionCounters()
{
  _console->println("Total transmission count: " + String(totalTransmissionCount));
  _console->println("Total successful transmissions: " + String(totalSuccessCount));
  _console->println("Total failed transmissions: " + String(totalFailedCount));

  _console->print("Spreading Factor counters: ");
  for (int i = MIN_SF; i <= MAX_SF; i++)
  {
    _console->print("SF");
    _console->print(i);
    _console->print("(");
    if (i + 1 == MAX_SF) {
      _console->print(transmissionCounters[i - MIN_SF]); 
      _console->println(")");
    } else {
      _console->print(transmissionCounters[i - MIN_SF]); 
      _console->print("), ");
    }
  }
}

FrameCounters BaseStrategy::fetchFrameCounters()
{
  char dnbuf[16];
  char upbuf[16];
  _loRaBee->getMacParam("dnctr", dnbuf, 16);
  _loRaBee->getMacParam("upctr", upbuf, 16);
  _console->print("Downlink frame counter: ");
  _console->println(dnbuf);
  _console->print("Uplink frame counter: ");
  _console->println(upbuf);

  // Convert char arrays to integers
  FrameCounters counters;
  counters.downlink = atoi(dnbuf);
  counters.uplink = atoi(upbuf);

  return counters;
}

void BaseStrategy::configureTransmission(const char *cr, uint8_t sf, uint8_t frq, uint8_t fsb)
{
  String message = "Config: CR:" + String(cr) + " SF:" + String(sf) + " FR:" + String(frq) + " CH:" + String(fsb);
  _console->println(message);

  _loRaBee->setSpreadingFactor(sf);
  _loRaBee->setPowerIndex(frq);
  _loRaBee->setFsbChannels(fsb);
  //_loRaBee->setCodingRate(cr); TODO doesn't work like this
}

bool BaseStrategy::handleErrorState(uint8_t res, uint8_t &count, int sf)
{
  totalTransmissionCount++;
  _console->print("LoRa transmission result: ");
  _console->println(res);

  bool isInErrorState = true;
  switch (res)
  {
  case NoError:
    isInErrorState = false;
    _console->println("Successful transmission.");
    totalSuccessCount++;
    _setRgbColor(0x00, 0xFF, 0x00);
    if (count == 255)
    {
      count = 0;
    }
    else
    {
      count++;
    }
    incrementTransmissionCount(sf);
    delay(10000);
    break;
  case NoResponse:
    _console->println("There was no response from the device. Sleeping for 10sec.");
    _setRgbColor(0xFF, 0xFF, 0x00);
    delay(10000);
    break;
  case Timeout:
    _console->println("Connection timed-out. Check your serial connection to the device! Sleeping for 10sec.");
    _setRgbColor(0xFF, 0xFF, 0x00);
    delay(20000);
    break;
  case PayloadSizeError:
    _console->println("The size of the payload is greater than allowed. Transmission failed!");
    _setRgbColor(0xFF, 0x00, 0x00);
    delay(10000);
    break;
  case InternalError:
    _console->println("Oh No! This shouldn't happen. Something is really wrong! Try restarting the device!\r\nThe program will now halt.");
    _setRgbColor(0xFF, 0x00, 0x00);
    while (1)
    {
    };
    break;
  case Busy:
    _console->println("The device is busy. Sleeping for 10 extra seconds.");
    _setRgbColor(0xFF, 0xFF, 0x00);
    delay(10000);
    break;
  case Silent:
    _console->println("The device is silent. Sleeping for 10 extra seconds.");
    _setRgbColor(0xFF, 0xFF, 0x00);
    delay(10000);
    break;
  case NoFreeChannel:
    _console->println("The device has no free channel. Sleeping for 10 extra seconds.");
    _setRgbColor(0xFF, 0x60, 0x00);
    delay(10000);
    break;
  case NetworkFatalError:
    _console->println("There is a non-recoverable error with the network connection. You should re-connect.\r\nThe program will now halt.");
    _setRgbColor(0xFF, 0x00, 0x00);
    while (1)
    {
    };
    break;
  case NotConnected:
    _console->println("The device is not connected to the network. Please connect to the network before attempting to send data.\r\nThe program will now halt.");
    _setRgbColor(0xFF, 0x00, 0x00);
    while (1)
    {
    };
    break;
  case NoAcknowledgment:
    _console->println("There was no acknowledgment sent back!");
    totalFailedCount++;
    _setRgbColor(0xFF, 0xB0, 0x50);
    incrementTransmissionCount(sf);
    delay(10000);
    break;
  default:
    _setRgbColor(0x00, 0x7F, 0xFF);
    break;
  }

  return isInErrorState;
}