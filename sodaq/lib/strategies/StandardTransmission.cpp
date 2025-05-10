#include "StandardTransmission.h"

StandardTransmission::StandardTransmission(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
    : TransmissionStrategy(console, loRaBee, setRgbColorCallback)
{
}

bool StandardTransmission::sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
  bool sentMessageSucessfully = true;

  _console->print("Sending message with standard transmission... : ");
  for (int i = 0; i < size - 1; i++)
  {
    _console->print((char)buffer[i]);
  }
  _console->println(count);

  configureTransmission(9, 1, 0);

  _setRgbColor(0x00, 0xFF, 0x7F);
  uint8_t res = _loRaBee->send(port, buffer, size);
  bool isInErrorState = handleErrorState(res, count);

  if (isInErrorState) {
    _console->println("Unsuccessful transmission. ");
    sentMessageSucessfully = false;
  }

  return sentMessageSucessfully;
}