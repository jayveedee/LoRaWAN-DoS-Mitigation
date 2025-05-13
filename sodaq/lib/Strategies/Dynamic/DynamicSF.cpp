#include "DynamicSF.h"

DynamicSF::DynamicSF(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
    : BaseDynamic(console, loRaBee, setRgbColorCallback)
{
}

bool DynamicSF::adjustParameter()
{
    sf++;
    if (sf > MAX_SF)
    {
        return false; // No more adjustments possible
    }
    return true;
}

void DynamicSF::resetParameter()
{
    sf = 9;
}

String DynamicSF::getParameterName()
{
    return "spreading factor";
}

String DynamicSF::getCurrentParameterValue()
{
    return String(sf);
}