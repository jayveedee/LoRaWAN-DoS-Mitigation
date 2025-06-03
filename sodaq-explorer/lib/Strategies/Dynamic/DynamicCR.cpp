#include "DynamicCR.h"

// TODO if continuing with this, refactor usage of mac commands and use radio instead
DynamicCR::DynamicCR(Stream *console, Stream *loraStream, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
    : BaseDynamic(console, loraStream, loRaBee, setRgbColorCallback)
{
}

bool DynamicCR::adjustParameter()
{
    crIndex++;
    if (crIndex > MAX_CR_INDEX)
    {
        return false; // No more adjustments possible
    }
    else
    {
        cr = codingRates[crIndex];
    }
    return true;
}

void DynamicCR::resetParameter()
{
    crIndex = 0;
    cr = codingRates[crIndex];
}

String DynamicCR::getParameterName()
{
    return "coding rate";
}

String DynamicCR::getCurrentParameterValue()
{
    return codingRates[crIndex];
}