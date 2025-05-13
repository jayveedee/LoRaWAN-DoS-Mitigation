#include "DynamicRetryTransmission.h"

DynamicRetryTransmission::DynamicRetryTransmission(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
    : DynamicTransmission(console, loRaBee, setRgbColorCallback)
{
}

bool DynamicRetryTransmission::sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
    _console->print("Sending message with dynamic retry strategy... : ");
    for (int i = 0; i < size - 1; i++)
    {
        _console->print((char)buffer[i]);
    }
    _console->println(count);

    return configureDynamicTransmission(true, port, buffer, size, count);
}
