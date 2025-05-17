#ifndef BASE_DYNAMIC_H
#define BASE_DYNAMIC_H

#include "../BaseStrategy.h"

class BaseDynamic : public BaseStrategy
{
protected:
    const uint8_t MAX_RETRIES = 3;
    const char *cr = "4/5";
    uint8_t sf = 9;
    uint8_t frq = 1;
    uint8_t fsb = 0;

    virtual bool adjustParameter() = 0;
    virtual void resetParameter() = 0;
    virtual String getParameterName() = 0;
    virtual String getCurrentParameterValue() = 0;

    bool configureDynamicTransmission(bool withRetry, uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count);

public:
    BaseDynamic(Stream *console, Stream *loraStream, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t));
    virtual bool sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count) override;
};

#endif