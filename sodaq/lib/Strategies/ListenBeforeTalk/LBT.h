#ifndef LBT_H
#define LBT_H

#include "../BaseStrategy.h"
#include "../../Sodaq_RN2483_Radio/Sodaq_RN2483_Radio.h"

// EU LoRaWAN uses 8 channels across different FSBs
#define MAX_CHANNEL_ATTEMPTS 8
#define MAX_RETRIES_PER_CHANNEL 3

class LBT : public BaseStrategy
{
private:
    Sodaq_RN2483_Radio *_radio;

    // Channel information for EU868 individual channels
    struct ChannelInfo
    {
        uint8_t channelId;  // LoRaWAN channel ID (0-7)
        uint32_t frequency; // Frequency in Hz
        uint8_t failures;   // Failure count
        unsigned long lastFailureTime;
    };

    // EU868 default channels 0-2, additional channels 3-7
    ChannelInfo channels[MAX_CHANNEL_ATTEMPTS] = {
        {0, 868100000, 0, 0}, // Channel 0: 868.1 MHz (default)
        {1, 868300000, 0, 0}, // Channel 1: 868.3 MHz (default)
        {2, 868500000, 0, 0}, // Channel 2: 868.5 MHz (default)
        {3, 867100000, 0, 0}, // Channel 3: 867.1 MHz
        {4, 867300000, 0, 0}, // Channel 4: 867.3 MHz
        {5, 867500000, 0, 0}, // Channel 5: 867.5 MHz
        {6, 867700000, 0, 0}, // Channel 6: 867.7 MHz
        {7, 867900000, 0, 0}  // Channel 7: 867.9 MHz
    };

    // Helper methods
    int selectBestChannel();
    void recordChannelFailure(uint8_t channelId);
    bool isChannelJammed(uint8_t channelId);
    bool configureChannelForTransmission(uint8_t channelId);

public:
    LBT(Stream *console, Stream *loraStream, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t));
    virtual bool sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count);
    virtual ~LBT();
};

#endif