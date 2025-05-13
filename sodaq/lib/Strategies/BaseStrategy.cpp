#include "BaseStrategy.h"

BaseStrategy::BaseStrategy(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
{
  _console = console;
  _loRaBee = loRaBee;
  _setRgbColor = setRgbColorCallback;
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
  char printbuf[64];
  sprintf(printbuf, "Initializing coding rate as %s, SF as %d, band rate as %d, channels as %d", cr, sf, frq, fsb);
  _console->println(printbuf);

  _loRaBee->setSpreadingFactor(sf);
  _loRaBee->setPowerIndex(frq);
  _loRaBee->setFsbChannels(fsb);
  _loRaBee->setCodingRate(cr);
}

bool BaseStrategy::handleErrorState(uint8_t res, uint8_t &count)
{
  _console->print("LoRa transmission result: ");
  _console->println(res);

  bool isInErrorState = true;
  switch (res)
  {
  case NoError:
    isInErrorState = false;
    _console->println("Successful transmission.");
    _setRgbColor(0x00, 0xFF, 0x00);
    if (count == 255)
    {
      count = 0;
    }
    else
    {
      count++;
    }
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
    _setRgbColor(0xFF, 0xB0, 0x50);
    delay(10000);
    break;
  default:
    _setRgbColor(0x00, 0x7F, 0xFF);
    break;
  }

  return isInErrorState;
}