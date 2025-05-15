#ifndef DYNAMIC_CR_H
#define DYNAMIC_CR_H

#include "BaseDynamic.h"

class DynamicCR : public BaseDynamic
{
protected:
    uint8_t crIndex = 0;
    const char *codingRates[4] = {"4/5", "4/6", "4/7", "4/8"};
    const uint8_t MAX_CR_INDEX = 3;

public:
    DynamicCR(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t));

protected:
    virtual bool adjustParameter() override;
    virtual void resetParameter() override;
    virtual String getParameterName() override;
    virtual String getCurrentParameterValue() override;
};

#endif