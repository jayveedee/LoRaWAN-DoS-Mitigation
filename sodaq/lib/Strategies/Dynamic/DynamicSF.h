#ifndef DYNAMIC_SF_H
#define DYNAMIC_SF_H

#include "BaseDynamic.h"

class DynamicSF : public BaseDynamic
{
protected:
    const uint8_t MAX_SF = 12;

public:
    DynamicSF(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t));

protected:
    virtual bool adjustParameter() override;
    virtual void resetParameter() override;
    virtual String getParameterName() override;
    virtual String getCurrentParameterValue() override;
};

#endif