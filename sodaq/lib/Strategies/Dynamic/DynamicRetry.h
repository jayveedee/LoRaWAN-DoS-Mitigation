#ifndef DYNAMIC_RETRY_H
#define DYNAMIC_RETRY_H

#include "BaseDynamic.h"

template <typename BaseDynamicRetry>
class DynamicRetry : public BaseDynamicRetry
{
public:
    DynamicRetry(Stream *console, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
        : BaseDynamicRetry(console, loRaBee, setRgbColorCallback)
    {
    }

    virtual bool sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count) override
    {
        this->_console->print("Sending message with dynamic retry ");
        this->_console->print(this->getParameterName());
        this->_console->print(" strategy... : ");
        for (int i = 0; i < size - 1; i++)
        {
            this->_console->print((char)buffer[i]);
        }
        this->_console->println(count);

        return this->configureDynamicTransmission(true, port, buffer, size, count);
    }
};

// Type aliases for convenience
using DynamicRetrySF = DynamicRetry<DynamicSF>;
using DynamicRetryCR = DynamicRetry<DynamicCR>;

#endif