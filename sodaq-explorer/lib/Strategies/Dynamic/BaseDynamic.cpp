#include "BaseDynamic.h"

BaseDynamic::BaseDynamic(Stream *console, Stream *loraStream, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
    : BaseStrategy(console, loraStream, loRaBee, setRgbColorCallback)
{
}

bool BaseDynamic::sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
    _console->print("Sending message with dynamic ");
    _console->print(getParameterName());
    _console->print(" strategy... : ");
    for (int i = 0; i < size - 1; i++)
    {
        _console->print((char)buffer[i]);
    }
    _console->println(count);

    return configureDynamicTransmission(false, port, buffer, size, count);
}

bool BaseDynamic::configureDynamicTransmission(bool withRetry, uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
    bool sentMessageSuccessfully = true;
    uint16_t transmissionAmount = withRetry ? MAX_RETRIES : 1;

    resetParameter(); // Start with default value
    uint8_t res = 0xFF;
    bool isInErrorState = false;

    while (res != NoError)
    {
        configureTransmission(cr, sf, frq, fsb);

        for (uint8_t i = 0; i < transmissionAmount - 1; i++)
        {
            _setRgbColor(0x00, 0xFF, 0x7F);
            incrementTransmissionCount(sf);
            res = _loRaBee->sendReqAck(port, buffer, size, 0);
            isInErrorState = handleErrorState(res, count);

            if (!isInErrorState)
            {
                break;
            }
            else if (res == NoAcknowledgment)
            {
                _console->print("Unsuccessful transmission because of NoAcknowledgement, retrying with same configuration up to a maxium of ");
                _console->print(transmissionAmount);
                _console->println(" retries.");
                fetchFrameCounters();
            }
            else
            {
                _console->println("Unsuccessful transmission because of other errors, retrying with same configuration without a max retry");
                fetchFrameCounters();
                i = i - 1;
            }
        }

        if (res == NoAcknowledgment && isInErrorState)
        {
            // Try adjusting the parameter
            if (!adjustParameter())
            {
                _console->print("Unsuccessful transmission. All ");
                _console->print(getParameterName());
                _console->println(" values tried.");
                sentMessageSuccessfully = false;
                break;
            }
            else
            {
                _console->print("Unsuccessful transmission, retrying with adjusted ");
                _console->print(getParameterName());
                _console->print(" to: ");
                _console->println(getCurrentParameterValue());
                fetchFrameCounters();
            }
        }
        else if (isInErrorState)
        {
            // Continue, maybe add max retry
        }
        else
        {
            break;
        }
    }

    return sentMessageSuccessfully;
}