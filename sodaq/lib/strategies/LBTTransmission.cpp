#include "LBTTransmission.h"

LBTTransmission::LBTTransmission(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
    : TransmissionStrategy(console, loRaBee, setRgbColorCallback)
{
  _rssiThreshold = DEFAULT_RSSI_THRESHOLD;
  _listenTimeout = DEFAULT_LISTEN_TIMEOUT;
  _maxRetryCount = DEFAULT_MAX_RETRY_COUNT;
  _dummyPayloadSize = DEFAULT_DUMMY_PAYLOAD_SIZE;

  // Initialize jamming stats
  _jammingStats.totalTransmissions = 0;
  _jammingStats.jammingDetected = 0;
  _jammingStats.lastJammingTime = 0;
  _jammingStats.currentChannel = DEFAULT_LORA_CHANNEL;
  _jammingStats.retryCount = 0;
}

bool LBTTransmission::detectJamming()
{
  _console->println("Using channel activity detection method");

  // Instead of listening with receive mode, we'll use the MAC state to infer channel activity
  // We'll attempt to do a very quick check of the channel

  // Attempt to get general MAC status
  char statusBuffer[16];
  _loRaBee->getMacParam("status", statusBuffer, sizeof(statusBuffer));
  _console->print("MAC status: ");
  _console->println(statusBuffer);

  // Use get SNR to estimate if the channel is jammed
  int8_t snr = _loRaBee->getSNR();
  int16_t rssi = _loRaBee->getRSSI();

  _console->print("Current RSSI: ");
  _console->println(rssi);
  _console->print("Current SNR: ");
  _console->println(snr);

  // Consider the channel jammed if the RSSI is higher than threshold
  bool jammingDetected = (rssi > _rssiThreshold);

  // Update jamming statistics
  _jammingStats.totalTransmissions++;

  if (jammingDetected)
  {
    _console->println("Channel appears to be jammed");
    _setRgbColor(0xFF, 0x00, 0x00); // Red
    _jammingStats.jammingDetected++;
    _jammingStats.lastJammingTime = millis();
  }
  else
  {
    _console->println("Channel appears to be clear");
    _setRgbColor(0x00, 0xFF, 0x00); // Green
  }

  return jammingDetected;
}

void LBTTransmission::implementMitigationStrategy()
{
  _console->println("Implementing jamming mitigation strategy");
  _setRgbColor(0xFF, 0xA5, 0x00); // Orange - Implementing mitigation

  // Strategy 1: Wait for a random backoff time
  int backoffTime = random(500, 3000); // Random backoff between 0.5-3 seconds
  _console->print("Backing off for ");
  _console->print(backoffTime);
  _console->println(" ms");
  delay(backoffTime);

  // Strategy 2: Try to change channel if possible
  byte newChannel = (_jammingStats.currentChannel + 1) % 8;
  uint32_t baseFrequency = 868100000;                            // Base frequency for 868MHz band
  uint32_t newFrequency = baseFrequency + (newChannel * 200000); // 200kHz spacing

  _console->print("Attempting to switch to channel ");
  _console->println(newChannel);

  if (_loRaBee->setChannel(newChannel, newFrequency))
  {
    _jammingStats.currentChannel = newChannel;
    _console->print("Successfully switched to channel: ");
    _console->println(newChannel);
  }
  else
  {
    _console->println("Channel change not possible at this time");
  }
}

bool LBTTransmission::sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
  bool sentMessageSucessfully = true;

  _setRgbColor(0xFF, 0xFF, 0x00);

  _jammingStats.retryCount = 0;

  _console->print("Sending message with LBT strategy... : ");
  for (int i = 0; i < size - 1; i++)
  {
    _console->print((char)buffer[i]);
  }
  _console->println(count);

  while (_jammingStats.retryCount < _maxRetryCount)
  {
    bool isJamming = detectJamming();

    if (!isJamming)
    {
      _console->println("No interference detected, proceeding with transmission");

      _setRgbColor(0xFF, 0xFF, 0x00);
      uint8_t result = _loRaBee->send(port, buffer, size);

      bool errorState = handleErrorState(result, count);

      if (!errorState)
      {
        sentMessageSucessfully = true;
        break;
      }
    }
    else
    {
      sentMessageSucessfully = false;
      implementMitigationStrategy();
    }

    _jammingStats.retryCount++;
    _console->print("Retry attempt: ");
    _console->println(_jammingStats.retryCount);
  }

  _console->println("Max retry count reached, transmission failed");
  _setRgbColor(0xFF, 0x00, 0x00);
  return sentMessageSucessfully;
}

void LBTTransmission::logJammingEvent()
{
  _console->println("--- Jamming Statistics ---");
  _console->print("Total transmissions: ");
  _console->println(_jammingStats.totalTransmissions);
  _console->print("Jamming events detected: ");
  _console->println(_jammingStats.jammingDetected);
  _console->print("Jamming rate: ");
  float jammingRate = (float)_jammingStats.jammingDetected / _jammingStats.totalTransmissions * 100.0;
  _console->print(jammingRate);
  _console->println("%");
  _console->print("Last jamming event: ");
  _console->print((millis() - _jammingStats.lastJammingTime) / 1000);
  _console->println(" seconds ago");
  _console->println("-------------------------");
}

JammingStats LBTTransmission::getJammingStats()
{
  return _jammingStats;
}

void LBTTransmission::resetJammingStats()
{
  _jammingStats.totalTransmissions = 0;
  _jammingStats.jammingDetected = 0;
  _jammingStats.lastJammingTime = 0;
  _jammingStats.retryCount = 0;
}