#include "RetryTransmission.h"

RetryTransmission::RetryTransmission(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t), uint8_t maxRetries)
    : TransmissionStrategy(console, loRaBee, setRgbColorCallback)
{
  _maxRetries = maxRetries;
}

void RetryTransmission::configureTransmission(uint8_t sf, uint8_t frq, uint8_t fsb)
{
  char printbuf[64];
  sprintf(printbuf, "Initializing SF as %d, band rate as %d, channels as %d", sf, frq, fsb);
  _console->println(printbuf);

  _loRaBee->setSpreadingFactor(sf);
  _loRaBee->setPowerIndex(frq);
  _loRaBee->setFsbChannels(fsb);
}

bool RetryTransmission::sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
  _setRgbColor(0xFF, 0xFF, 0x00);

  _console->print("Sending message with retry strategy... : ");
  for (int i = 0; i < size - 1; i++)
  {
    _console->print((char)buffer[i]);
  }
  _console->println(count);

  configureTransmission(9, 1, 0);
  uint8_t res = _loRaBee->sendReqAck(port, buffer, size, _maxRetries);
  bool isInErrorState = handleErrorState(res, count);

  return !isInErrorState;
}