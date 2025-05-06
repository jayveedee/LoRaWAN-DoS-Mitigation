#include "TransmissionStrategy.h"

TransmissionStrategy::TransmissionStrategy(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
{
  _console = console;
  _loRaBee = loRaBee;
  _setRgbColor = setRgbColorCallback;
}

void TransmissionStrategy::fetchFrameCounters()
{
  char dnbuf[16];
  char upbuf[16];

  _loRaBee->getMacParam("dnctr", dnbuf, 16);
  _loRaBee->getMacParam("upctr", upbuf, 16);

  _console->print("Downlink frame counter: ");
  _console->println(dnbuf);
  _console->print("Uplink frame counter: ");
  _console->println(upbuf);
}

bool TransmissionStrategy::handleErrorState(uint8_t res, uint8_t &count)
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
    _console->println("There was no response from the device.");
    _setRgbColor(0xFF, 0x00, 0x00);
    break;
  case Timeout:
    _console->println("Connection timed-out. Check your serial connection to the device! Sleeping for 20sec.");
    _setRgbColor(0xFF, 0xA5, 0x00);
    delay(20000);
    break;
  case PayloadSizeError:
    _console->println("The size of the payload is greater than allowed. Transmission failed!");
    _setRgbColor(0xFF, 0x00, 0x00);
    delay(10000);
    break;
  case InternalError:
    _console->println("Oh No! This shouldn't happen. Something is really wrong! Try restarting the device!\r\nThe program will now halt.");
    while (1)
    {
      _setRgbColor(0xFF, 0xA5, 0x00);
      delay(250);
      _setRgbColor(0xFF, 0x00, 0x00);
      delay(250);
    };
    break;
  case Busy:
    _console->println("The device is busy. Sleeping for 10 extra seconds.");
    _setRgbColor(0xFF, 0xA5, 0x00);
    delay(10000);
    break;
  case Silent:
    _console->println("The device is silent. Sleeping for 10 extra seconds.");
    _setRgbColor(0xFF, 0xA5, 0x00);
    delay(10000);
    break;
  case NoFreeChannel:
    _console->println("The device has no free channel. Sleeping for 10 extra seconds.");
    _setRgbColor(0xFF, 0xA5, 0x00);
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
    _setRgbColor(0xFF, 0x00, 0x00);
    delay(10000);
    break;
  default:
    _setRgbColor(0x00, 0x00, 0x00);
    break;
  }

  return isInErrorState;
}