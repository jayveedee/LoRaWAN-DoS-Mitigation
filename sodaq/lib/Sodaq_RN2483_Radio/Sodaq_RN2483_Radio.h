#ifndef SODAQ_RN2483_RADIO_H
#define SODAQ_RN2483_RADIO_H

#include <Arduino.h>

class Sodaq_RN2483_Radio
{
private:
    Stream *_console;
    Stream *_loraStream;

    bool sendCommand(const char *command, char *response = nullptr, size_t responseSize = 0, unsigned long timeout = 1000);
    bool readLine(char *buffer, size_t size, unsigned long timeout = 1000);
    void flushInput();
    bool listenForInterference(int durationMs = 1000);
    bool analyzeTransmissionTiming();
    bool testRadioBehaviorConsistency();

public:
    Sodaq_RN2483_Radio(Stream *console, Stream *loraStream);

    // MAC layer control
    bool pauseMac(unsigned long &pauseTimeMs);
    bool resumeMac();

    // Radio configuration
    bool setFrequency(uint32_t frequencyHz);
    bool setLoRaMode(int spreadingFactor = 9, int bandwidth = 125, const char *codingRate = "4/5", uint8_t syncWord = 34);

    // Radio operations
    bool transmit(const char *hexData);
    bool startReceive(int symbols = 0); // 0 = continuous
    bool stopReceive();

    // Check for received packets (non-blocking)
    enum ReceiveResult
    {
        RX_NOTHING,
        RX_PACKET,
        RX_TIMEOUT,
        RX_ERROR
    };

    ReceiveResult checkReceive(char *packetData = nullptr, size_t dataSize = 0);

    // Simple jammer detection for one frequency
    bool detectJammerOnFrequency(uint32_t frequencyHz, int timeoutMs = 5000);

    // EU868 specific channel configuration (bypassing FSB system)
    bool configureEU868Channel(uint8_t channelId, uint32_t frequencyHz);
    bool enableOnlyChannel(uint8_t channelId);
    bool setChannelFrequency(uint8_t channelId, uint32_t frequencyHz);
    bool setChannelDataRateRange(uint8_t channelId, uint8_t minDR, uint8_t maxDR);
    bool setChannelStatus(uint8_t channelId, bool enabled);
    bool saveConfiguration();
    bool verifyChannelConfiguration(uint8_t channelId);
};

#endif