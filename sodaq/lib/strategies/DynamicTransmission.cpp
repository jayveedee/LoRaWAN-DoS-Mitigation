
//TODO add coding rate stuff
#include "DynamicTransmission.h"

DynamicTransmission::DynamicTransmission(Stream* console, Sodaq_RN2483* loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
    : TransmissionStrategy(console, loRaBee, setRgbColorCallback) {
}

void DynamicTransmission::configureTransmission(uint8_t sf, uint8_t frq, uint8_t fsb) {
  char printbuf[64];
  sprintf(printbuf, "Initializing SF as %d, band rate as %d, channels as %d", sf, frq, fsb);
  _console->println(printbuf);

  _loRaBee->setSpreadingFactor(sf);
  _loRaBee->setPowerIndex(frq);
  _loRaBee->setFsbChannels(fsb);
}

bool DynamicTransmission::sendMessage(uint8_t port, uint8_t* buffer, uint8_t size, uint8_t& count) {
  _setRgbColor(0xFF, 0xFF, 0x00);
  
  _console->print("Sending message with dynamic SF strategy... : ");
  for (int i = 0; i < size - 1; i++) {  
    _console->print((char)buffer[i]);  
  }
  _console->println(count);

  uint8_t sf = 9;
  uint8_t frq = 1;
  uint8_t fsb = 0;
  uint8_t res = 0xFF; // Initialize with error
  bool isInErrorState = true;
  
  while (res != NoError && sf <= 12) {
    configureTransmission(sf, frq, fsb);
    res = _loRaBee->sendReqAck(port, buffer, size, 0);
    isInErrorState = handleErrorState(res, count);
    
    if (isInErrorState) {
      sf++;
      if (sf > 12) {
        _console->println("Unsuccessful transmission.");
        break;
      } else {
        _console->print("Unsuccessful transmission, retrying and incrementing spreading factor to: ");
        _console->println(sf);
        fetchFrameCounters();
      }
    } else {
      break;
    }
  }
  
  return !isInErrorState;
}