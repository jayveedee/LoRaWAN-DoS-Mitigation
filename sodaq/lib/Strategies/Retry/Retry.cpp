#include "Retry.h"

Retry::Retry(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t), uint8_t maxRetries)
    : BaseStrategy(console, loRaBee, setRgbColorCallback)
{
  _maxRetries = maxRetries;
}

bool Retry::sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
  bool sentMessageSucessfully = true;

  _console->print("Sending message with retry strategy... : ");
  for (int i = 0; i < size - 1; i++)
  {
    _console->print((char)buffer[i]);
  }
  _console->println(count);

  configureTransmission("4/5", 9, 1, 0);

  _setRgbColor(0x00, 0xFF, 0x7F);
  uint8_t res = _loRaBee->sendReqAck(port, buffer, size, _maxRetries);
  bool isInErrorState = handleErrorState(res, count);

  if (isInErrorState)
  {
    _console->println("Unsuccessful transmission. ");
    sentMessageSucessfully = false;
  }

  return sentMessageSucessfully;
}