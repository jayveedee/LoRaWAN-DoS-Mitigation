
// TODO add coding rate stuff
#include "DynamicTransmission.h"

DynamicTransmission::DynamicTransmission(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
    : TransmissionStrategy(console, loRaBee, setRgbColorCallback)
{
}

bool DynamicTransmission::sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
  bool sentMessageSucessfully = true;

  _console->print("Sending message with dynamic strategy... : ");
  for (int i = 0; i < size - 1; i++)
  {
    _console->print((char)buffer[i]);
  }
  _console->println(count);

  uint8_t sf = 9;
  uint8_t frq = 1;
  uint8_t fsb = 0;
  uint8_t res = 0xFF; // Initialize with error

  while (res != NoError && sf <= 12)
  {
    configureTransmission(sf, frq, fsb);

    _setRgbColor(0x00, 0xFF, 0x7F);
    res = _loRaBee->sendReqAck(port, buffer, size, 0);
    bool isInErrorState = handleErrorState(res, count);

    if (isInErrorState)
    {
      sf++;
      if (sf > 12)
      {
        _console->println("Unsuccessful transmission.");
        sentMessageSucessfully = false;
        break;
      }
      else
      {
        _console->print("Unsuccessful transmission, retrying and incrementing spreading factor to: ");
        _console->println(sf);
        fetchFrameCounters();
      }
    }
    else
    {
      break;
    }
  }

  return sentMessageSucessfully;
}