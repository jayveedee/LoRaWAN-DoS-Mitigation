#include "LBT.h"

LBT::LBT(Stream *console, Stream *loraStream, Sodaq_RN2483 *loRaBee, void (*setRgbColorCallback)(uint8_t, uint8_t, uint8_t))
    : BaseStrategy(console, loraStream, loRaBee, setRgbColorCallback)
{
    _radio = new Sodaq_RN2483_Radio(console, loraStream);
    _console->println("LBT: Initialized for EU868 (8 individual channels)");
}

LBT::~LBT()
{
    delete _radio;
}

bool LBT::sendMessage(uint8_t port, uint8_t *buffer, uint8_t size, uint8_t &count)
{
    _console->println("LBT: Starting transmission with channel-specific jammer detection");

    // Try channels until we find a clear one
    for (int attempt = 0; attempt < MAX_CHANNEL_ATTEMPTS; attempt++)
    {
        int channelIndex = selectBestChannel();
        uint8_t channelId = channels[channelIndex].channelId;
        uint32_t frequency = channels[channelIndex].frequency;

        _console->print("LBT: Testing channel ");
        _console->print(channelId);
        _console->print(" (");
        _console->print(frequency / 1000000.0, 1);
        _console->println(" MHz)");

        // Pause MAC for radio operations
        unsigned long pauseTime = 0;
        if (!_radio->pauseMac(pauseTime))
        {
            _console->println("LBT: Failed to pause MAC, proceeding without LBT");
            break;
        }

        if (pauseTime < 3000)
        {
            _console->println("LBT: Limited pause time, assuming channel is clear");
            _radio->resumeMac();
            break;
        }

        if (pauseTime > 4200000000UL)
        {
            _console->println("LBT: MAC in idle state - plenty of time for detection");
        }

        // Check if this specific channel is jammed
        bool jammed = isChannelJammed(channelId);

        // Resume MAC layer BEFORE configuring channels
        _radio->resumeMac();

        if (!jammed)
        {
            _console->print("LBT: Channel ");
            _console->print(channelId);
            _console->println(" is clear, configuring for transmission");

            // Configure LoRaWAN to use only this specific channel
            // Do this AFTER resuming MAC but BEFORE transmission attempts
            if (configureChannelForTransmission(channelId))
            {

                // Verify configuration took effect
                _radio->verifyChannelConfiguration(channelId);

                // Now attempt transmission with proper error handling
                _console->println("LBT: Starting transmission attempts...");

                for (int retry = 0; retry < MAX_RETRIES_PER_CHANNEL; retry++)
                {
                    _console->print("LBT: Transmission attempt ");
                    _console->print(retry + 1);
                    _console->print("/");
                    _console->println(MAX_RETRIES_PER_CHANNEL);

                    incrementTransmissionCount(9);
                    uint8_t result = _loRaBee->send(port, buffer, size);
                    bool isError = handleErrorState(result, count);

                    if (!isError)
                    {
                        _console->println("LBT: Message sent successfully!");
                        return true;
                    }

                    _console->print("LBT: Transmission failed with error code: ");
                    _console->println(result);

                    // Add delay between retries
                    if (retry < MAX_RETRIES_PER_CHANNEL - 1)
                    {
                        delay(random(1000, 2000)); // Longer delay for stability
                    }
                }

                _console->println("LBT: Transmission failed despite clear channel");
                recordChannelFailure(channelId);
            }
            else
            {
                _console->println("LBT: Failed to configure channel, trying next");
                recordChannelFailure(channelId);
            }
        }
        else
        {
            _console->print("LBT: Channel ");
            _console->print(channelId);
            _console->println(" is jammed, trying next channel");
            recordChannelFailure(channelId);
        }

        delay(200);
    }

    _console->println("LBT: Failed to send message - all EU channels appear jammed or unusable");
    return false;
}

bool LBT::configureChannelForTransmission(uint8_t channelId)
{
    _console->print("LBT: Configuring LoRaWAN for transmission on channel ");
    _console->println(channelId);

    uint32_t frequency = channels[channelId].frequency;

    // Use our radio wrapper to configure the channel properly
    if (!_radio->configureEU868Channel(channelId, frequency))
    {
        _console->println("LBT: Failed to configure channel parameters");
        return false;
    }

    // Enable only this channel for transmission
    if (!_radio->enableOnlyChannel(channelId))
    {
        _console->println("LBT: Failed to enable only target channel");
        return false;
    }

    // Give the module time to process channel configuration
    delay(500);

    // Configure basic LoRaWAN parameters using available Sodaq_RN2483 methods
    // Set spreading factor to SF9 for good balance of range/speed
    if (!_loRaBee->setSpreadingFactor(9))
    {
        _console->println("LBT: Failed to set spreading factor");
        return false;
    }

    // Set power index to 1 (14 dBm for EU868)
    if (!_loRaBee->setPowerIndex(1))
    {
        _console->println("LBT: Failed to set power index");
        return false;
    }

    // Save the configuration to module's EEPROM
    if (!_radio->saveConfiguration())
    {
        _console->println("LBT: Warning - failed to save configuration");
        // Don't fail completely, just warn
    }

    // Additional delay to ensure configuration is fully applied
    delay(200);

    _console->println("LBT: Channel configuration completed successfully");
    return true;
}

bool LBT::isChannelJammed(uint8_t channelId)
{
    uint32_t frequency = channels[channelId].frequency;

    _console->print("LBT: Probing channel ");
    _console->print(channelId);
    _console->print(" for jamming activity...");

    // Use the radio wrapper to detect jammer on this specific frequency
    bool jammed = _radio->detectJammerOnFrequency(frequency, 4000);

    _console->print(" Result: ");
    _console->println(jammed ? "JAMMED" : "CLEAR");

    return jammed;
}

int LBT::selectBestChannel()
{
    int bestChannel = 0;
    uint8_t lowestFailures = UINT8_MAX;

    _console->println("LBT: Channel failure history:");

    for (int i = 0; i < MAX_CHANNEL_ATTEMPTS; i++)
    {
        // Reset old failures (older than 30 minutes)
        if (channels[i].failures > 0 &&
            (millis() - channels[i].lastFailureTime) > 1800000)
        {
            _console->print("LBT: Resetting old failures for channel ");
            _console->println(channels[i].channelId);
            channels[i].failures = 0;
        }

        _console->print("LBT:   Channel ");
        _console->print(channels[i].channelId);
        _console->print(" (");
        _console->print(channels[i].frequency / 1000000.0, 1);
        _console->print(" MHz): ");
        _console->print(channels[i].failures);
        _console->println(" failures");

        if (channels[i].failures < lowestFailures)
        {
            lowestFailures = channels[i].failures;
            bestChannel = i;
        }
    }

    _console->print("LBT: Selected channel ");
    _console->print(channels[bestChannel].channelId);
    _console->print(" (");
    _console->print(channels[bestChannel].frequency / 1000000.0, 1);
    _console->print(" MHz, ");
    _console->print(lowestFailures);
    _console->println(" failures)");

    return bestChannel;
}

void LBT::recordChannelFailure(uint8_t channelId)
{
    for (int i = 0; i < MAX_CHANNEL_ATTEMPTS; i++)
    {
        if (channels[i].channelId == channelId)
        {
            if (channels[i].failures < UINT8_MAX)
            {
                channels[i].failures++;
            }
            channels[i].lastFailureTime = millis();

            _console->print("LBT: Recorded failure for channel ");
            _console->print(channelId);
            _console->print(" (total: ");
            _console->print(channels[i].failures);
            _console->println(")");
            break;
        }
    }
}