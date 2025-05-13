
// TODO add coding rate stuff
#include "DynamicTransmission.h"

DynamicTransmission::DynamicTransmission(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
    : TransmissionStrategy(console, loRaBee, setRgbColorCallback)
{
}

bool DynamicTransmission::sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
  _console->print("Sending message with dynamic strategy... : ");
  for (int i = 0; i < size - 1; i++)
  {
    _console->print((char)buffer[i]);
  }
  _console->println(count);

  return configureDynamicTransmission(false, port, buffer, size, count);
}

bool DynamicTransmission::configureDynamicTransmission(bool withRetry, uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
  bool sentMessageSucessfully = true;

  uint16_t retries = withRetry ? 3 : 0;

  while (res != NoError && sf <= 12)
  {
    configureTransmission(sf, frq, fsb);

    _setRgbColor(0x00, 0xFF, 0x7F);
    res = _loRaBee->sendReqAck(port, buffer, size, retries); // need to use same frame counter later if possible
    bool isInErrorState = handleErrorState(res, count);

    if (res == NoAcknowledgment && isInErrorState)
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
    else if (isInErrorState)
    {
      // Continue, maybe add max retry
    }
    else
    {
      break;
    }
  }

  return sentMessageSucessfully;
}