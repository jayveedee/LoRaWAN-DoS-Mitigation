#include "Sodaq_RN2483_Radio.h"

Sodaq_RN2483_Radio::Sodaq_RN2483_Radio(Stream *console, Stream *loraStream)
    : _console(console), _loraStream(loraStream)
{
}

bool Sodaq_RN2483_Radio::pauseMac(unsigned long &pauseTimeMs)
{
    char response[32];

    flushInput();
    _console->println("Radio: Pausing MAC layer");

    // Send mac pause command
    _loraStream->print("mac pause\r\n");

    if (readLine(response, sizeof(response), 1000))
    {
        _console->print("Radio: MAC pause response: ");
        _console->println(response);

        if (strcmp(response, "ok") == 0)
        {
            // Read the pause time
            if (readLine(response, sizeof(response), 1000))
            {
                pauseTimeMs = strtoul(response, nullptr, 10);
                _console->print("Radio: Paused for ");
                _console->print(pauseTimeMs);
                _console->println(" ms");

                // Large values indicate idle state (which is good)
                if (pauseTimeMs > 4200000000UL)
                {
                    _console->println("Radio: MAC is in idle state - can pause indefinitely");
                }
                return true;
            }
        }
        else
        {
            // Sometimes the response IS the pause time directly (no "ok" first)
            pauseTimeMs = strtoul(response, nullptr, 10);
            if (pauseTimeMs > 0)
            {
                _console->print("Radio: Paused for ");
                _console->print(pauseTimeMs);
                _console->println(" ms");

                if (pauseTimeMs > 4200000000UL)
                {
                    _console->println("Radio: MAC is in idle state - can pause indefinitely");
                }
                return true;
            }
        }
    }

    _console->println("Radio: Failed to pause MAC");
    pauseTimeMs = 0;
    return false;
}

bool Sodaq_RN2483_Radio::resumeMac()
{
    char response[16];

    flushInput();
    _console->println("Radio: Resuming MAC layer");

    _loraStream->print("mac resume\r\n");

    if (readLine(response, sizeof(response), 1000))
    {
        bool success = (strcmp(response, "ok") == 0);
        _console->print("Radio: MAC resume result: ");
        _console->println(success ? "OK" : "FAILED");
        return success;
    }

    return false;
}

bool Sodaq_RN2483_Radio::setFrequency(uint32_t frequencyHz)
{
    char command[32];
    char response[16];

    sprintf(command, "radio set freq %lu", frequencyHz);
    return sendCommand(command, response, sizeof(response));
}

bool Sodaq_RN2483_Radio::setLoRaMode(int spreadingFactor, int bandwidth, const char *codingRate, uint8_t syncWord)
{
    char response[16];
    char command[32];

    // Set all LoRa parameters
    if (!sendCommand("radio set mod lora", response, sizeof(response)))
        return false;

    sprintf(command, "radio set sf sf%d", spreadingFactor);
    if (!sendCommand(command, response, sizeof(response)))
        return false;

    sprintf(command, "radio set bw %d", bandwidth);
    if (!sendCommand(command, response, sizeof(response)))
        return false;

    sprintf(command, "radio set cr %s", codingRate);
    if (!sendCommand(command, response, sizeof(response)))
        return false;

    sprintf(command, "radio set sync %d", static_cast<unsigned int>(syncWord));
    if (!sendCommand(command, response, sizeof(response)))
        return false;

    return true;
}

bool Sodaq_RN2483_Radio::transmit(const char *hexData)
{
    char command[128];
    char response[32];

    _console->print("Radio: DEBUG - Sending command: ");
    sprintf(command, "radio tx %s", hexData);
    _console->println(command);

    flushInput(); // Clear any pending input first

    _loraStream->print(command);
    _loraStream->print("\r\n");

    _console->println("Radio: DEBUG - Waiting for first response...");

    // Wait for first response (ok/invalid_param/busy)
    if (readLine(response, sizeof(response), 2000)) // Increased timeout
    {
        _console->print("Radio: DEBUG - First response received: '");
        _console->print(response);
        _console->println("'");

        if (strcmp(response, "ok") == 0)
        {
            _console->println("Radio: DEBUG - Got OK, waiting for TX completion...");

            // Wait for second response (radio_tx_ok/radio_err)
            if (readLine(response, sizeof(response), 8000)) // Longer timeout for TX
            {
                _console->print("Radio: DEBUG - Second response received: '");
                _console->print(response);
                _console->println("'");

                // Success only if we get "radio_tx_ok"
                if (strcmp(response, "radio_tx_ok") == 0)
                {
                    _console->println("Radio: DEBUG - SUCCESS!");
                    return true; // SUCCESS
                }
                else if (strcmp(response, "radio_err") == 0)
                {
                    _console->println("Radio: DEBUG - Transmission error");
                    return false; // FAILED
                }
                else
                {
                    _console->print("Radio: DEBUG - Unexpected second response: '");
                    _console->print(response);
                    _console->println("'");
                    return false; // FAILED
                }
            }
            else
            {
                _console->println("Radio: DEBUG - Timeout waiting for TX completion");
                return false; // FAILED
            }
        }
        else if (strcmp(response, "invalid_param") == 0)
        {
            _console->println("Radio: DEBUG - Invalid parameter");
            return false;
        }
        else if (strcmp(response, "busy") == 0)
        {
            _console->println("Radio: DEBUG - Radio busy");
            return false;
        }
        else
        {
            _console->print("Radio: DEBUG - Unexpected first response: '");
            _console->print(response);
            _console->println("'");
            return false; // FAILED
        }
    }
    else
    {
        _console->println("Radio: DEBUG - No response to TX command (timeout)");
        return false; // FAILED
    }
}

bool Sodaq_RN2483_Radio::startReceive(int symbols)
{
    char command[32];
    char response[16];

    sprintf(command, "radio rx %d", symbols);
    _loraStream->print(command);
    _loraStream->print("\r\n");

    if (readLine(response, sizeof(response), 1000))
    {
        return (strcmp(response, "ok") == 0);
    }

    return false;
}

bool Sodaq_RN2483_Radio::stopReceive()
{
    char response[16];

    _loraStream->print("radio sleep\r\n");
    if (readLine(response, sizeof(response), 500))
    {
        return (strcmp(response, "ok") == 0);
    }

    return false;
}

Sodaq_RN2483_Radio::ReceiveResult Sodaq_RN2483_Radio::checkReceive(char *packetData, size_t dataSize)
{
    char response[128];

    // Non-blocking check for received data
    if (readLine(response, sizeof(response), 100))
    {
        if (strncmp(response, "radio_rx", 8) == 0)
        {
            if (packetData && dataSize > 0)
            {
                strncpy(packetData, response, dataSize - 1);
                packetData[dataSize - 1] = '\0';
            }
            return RX_PACKET;
        }
        else if (strcmp(response, "radio_err") == 0)
        {
            return RX_TIMEOUT;
        }
    }

    return RX_NOTHING;
}

// Jammer detection methods that work without a receiver
bool Sodaq_RN2483_Radio::detectJammerOnFrequency(uint32_t frequencyHz, int timeoutMs)
{
    _console->print("Radio: No-receiver jammer detection on ");
    _console->print(frequencyHz / 1000000.0, 1);
    _console->println(" MHz");

    // Configure radio
    if (!setFrequency(frequencyHz) || !setLoRaMode(9, 125, "4/5", 34))
    {
        _console->println("Radio: Configuration failed");
        return false;
    }

    int jammerScore = 0;

    // Method 1: Listen for unexpected activity/interference
    _console->println("Radio: Method 1 - Listening for interference");
    bool interferenceHeard = listenForInterference(3000);

    if (interferenceHeard)
    {
        _console->println("Radio: DETECTED - Channel activity/interference");
        jammerScore += 2; // Strong indicator
    }
    else
    {
        _console->println("Radio: Channel appears quiet");
    }

    // Method 2: Transmission timing analysis
    _console->println("Radio: Method 2 - Analyzing transmission timing");
    bool timingAnomalies = analyzeTransmissionTiming();

    if (timingAnomalies)
    {
        _console->println("Radio: DETECTED - Transmission timing anomalies");
        jammerScore += 1;
    }
    else
    {
        _console->println("Radio: Normal transmission timing");
    }

    // Method 3: Radio behavior consistency test
    _console->println("Radio: Method 3 - Testing radio behavior consistency");
    bool behaviorInconsistent = testRadioBehaviorConsistency();

    if (behaviorInconsistent)
    {
        _console->println("Radio: DETECTED - Inconsistent radio behavior");
        jammerScore += 1;
    }
    else
    {
        _console->println("Radio: Consistent radio behavior");
    }

    // Decision logic
    bool jammerDetected = (jammerScore >= 2);

    _console->print("Radio: Jammer score: ");
    _console->print(jammerScore);
    _console->print("/4 - ");
    _console->println(jammerDetected ? "JAMMED" : "CLEAR");

    return jammerDetected;
}

// Listen for any RF activity that might indicate jamming
bool Sodaq_RN2483_Radio::listenForInterference(int durationMs)
{
    _console->println("Radio: Starting interference listening...");

    int activityCount = 0;
    int listenAttempts = 0;
    unsigned long startTime = millis();

    while (millis() - startTime < durationMs)
    {
        // Start a brief receive window
        if (startReceive(3)) // Very short window - 3 symbols
        {
            listenAttempts++;

            // Wait for the receive window
            delay(300);

            ReceiveResult result = checkReceive();

            if (result == RX_PACKET)
            {
                activityCount++;
                _console->println("Radio: Detected packet/activity");

                // Try to get SNR of whatever we received
                char response[32];
                if (sendCommand("radio get snr", response, sizeof(response), 500))
                {
                    int snr = atoi(response);
                    _console->print("Radio: Activity SNR: ");
                    _console->println(snr);

                    // Very high SNR might indicate strong local interference
                    if (snr > 5)
                    {
                        _console->println("Radio: Strong local signal detected");
                        activityCount += 2; // Bonus for strong signals
                    }
                }
            }

            stopReceive();
        }

        delay(200);
    }

    _console->print("Radio: Activity detected in ");
    _console->print(activityCount);
    _console->print(" out of ");
    _console->print(listenAttempts);
    _console->println(" listen attempts");

    // If we detect activity when channel should be quiet, might be jammer
    return (activityCount > 0 && listenAttempts > 5);
}

// Analyze if transmission timing is affected by interference
bool Sodaq_RN2483_Radio::analyzeTransmissionTiming()
{
    _console->println("Radio: Analyzing transmission timing");

    unsigned long timings[5];
    bool timingValid[5];

    for (int i = 0; i < 5; i++)
    {
        char testData[16];
        sprintf(testData, "010203040%04X", (unsigned int)(millis() & 0xFFFF));

        unsigned long startTime = millis();

        // Send the transmission
        char command[64];
        char response[32];
        sprintf(command, "radio tx %s", testData);

        flushInput();
        _loraStream->print(command);
        _loraStream->print("\r\n");

        // Time how long until we get the completion response
        bool gotOk = false;
        if (readLine(response, sizeof(response), 2000))
        {
            if (strcmp(response, "ok") == 0)
            {
                gotOk = true;
                // Now wait for completion
                if (readLine(response, sizeof(response), 8000))
                {
                    unsigned long endTime = millis();
                    timings[i] = endTime - startTime;
                    timingValid[i] = true;

                    _console->print("Radio: TX ");
                    _console->print(i + 1);
                    _console->print(" timing: ");
                    _console->print(timings[i]);
                    _console->print("ms (");
                    _console->print(response);
                    _console->println(")");
                }
                else
                {
                    timingValid[i] = false;
                    _console->print("Radio: TX ");
                    _console->print(i + 1);
                    _console->println(" - timeout");
                }
            }
            else
            {
                timingValid[i] = false;
                _console->print("Radio: TX ");
                _console->print(i + 1);
                _console->print(" - ");
                _console->println(response);
            }
        }
        else
        {
            timingValid[i] = false;
            _console->print("Radio: TX ");
            _console->print(i + 1);
            _console->println(" - no response");
        }

        delay(500);
    }

    // Analyze timing consistency
    int validCount = 0;
    unsigned long totalTime = 0;
    unsigned long minTime = 20000;
    unsigned long maxTime = 0;

    for (int i = 0; i < 5; i++)
    {
        if (timingValid[i])
        {
            validCount++;
            totalTime += timings[i];
            if (timings[i] < minTime)
                minTime = timings[i];
            if (timings[i] > maxTime)
                maxTime = timings[i];
        }
    }

    if (validCount >= 3)
    {
        unsigned long avgTime = totalTime / validCount;
        unsigned long timeSpread = maxTime - minTime;

        _console->print("Radio: Timing analysis - avg: ");
        _console->print(avgTime);
        _console->print("ms, spread: ");
        _console->print(timeSpread);
        _console->print("ms, valid: ");
        _console->print(validCount);
        _console->println("/5");

        // Large timing variations or many failures might indicate interference
        return (timeSpread > 2000 || validCount < 4);
    }
    else
    {
        _console->println("Radio: Too many timing failures - possible interference");
        return true;
    }
}

// Test if radio behavior is consistent (interference can cause erratic behavior)
bool Sodaq_RN2483_Radio::testRadioBehaviorConsistency()
{
    _console->println("Radio: Testing radio behavior consistency");

    int inconsistencies = 0;

    // Test 1: Multiple identical transmissions should behave similarly
    for (int i = 0; i < 3; i++)
    {
        const char *testData = "01020304";

        char command[64];
        char response[32];
        sprintf(command, "radio tx %s", testData);

        flushInput();
        _loraStream->print(command);
        _loraStream->print("\r\n");

        // First response
        bool gotOk = false;
        if (readLine(response, sizeof(response), 2000))
        {
            if (strcmp(response, "ok") == 0)
            {
                gotOk = true;
                // Second response
                if (readLine(response, sizeof(response), 8000))
                {
                    _console->print("Radio: Consistency test ");
                    _console->print(i + 1);
                    _console->print(": ");
                    _console->println(response);

                    if (strcmp(response, "radio_tx_ok") != 0)
                    {
                        inconsistencies++;
                    }
                }
                else
                {
                    _console->print("Radio: Consistency test ");
                    _console->print(i + 1);
                    _console->println(": timeout");
                    inconsistencies++;
                }
            }
            else
            {
                _console->print("Radio: Consistency test ");
                _console->print(i + 1);
                _console->print(": ");
                _console->println(response);
                inconsistencies++;
            }
        }
        else
        {
            _console->print("Radio: Consistency test ");
            _console->print(i + 1);
            _console->println(": no response");
            inconsistencies++;
        }

        delay(400);
    }

    _console->print("Radio: Behavior inconsistencies: ");
    _console->print(inconsistencies);
    _console->println("/3");

    return (inconsistencies >= 2);
}

bool Sodaq_RN2483_Radio::configureEU868Channel(uint8_t channelId, uint32_t frequencyHz)
{
    _console->print("Radio: Configuring EU868 channel ");
    _console->print(channelId);
    _console->print(" to ");
    _console->print(frequencyHz);
    _console->println(" Hz");

    // For channels 3-7, we need to set frequency first
    if (channelId >= 3)
    {
        if (!setChannelFrequency(channelId, frequencyHz))
        {
            return false;
        }
    }

    // Set data rate range (DR0-DR5 for EU868)
    if (!setChannelDataRateRange(channelId, 0, 5))
    {
        return false;
    }

    // Enable the channel
    return setChannelStatus(channelId, true);
}

bool Sodaq_RN2483_Radio::enableOnlyChannel(uint8_t channelId)
{
    _console->print("Radio: Enabling only channel ");
    _console->println(channelId);

    // EU868 has channels 0-2 (default) and 3-7 (configurable)
    // Only try to configure channels that actually exist
    bool targetChannelEnabled = false;

    for (uint8_t i = 0; i < 8; i++)
    {
        bool enable = (i == channelId);

        _console->print("Radio: Setting channel ");
        _console->print(i);
        _console->print(" to ");
        _console->println(enable ? "enabled" : "disabled");

        if (setChannelStatus(i, enable))
        {
            if (enable)
            {
                targetChannelEnabled = true;
                _console->print("Radio: Successfully enabled target channel ");
                _console->println(channelId);
            }
        }
        else
        {
            // Don't fail completely - some channels might not be configurable
            _console->print("Radio: Warning - could not configure channel ");
            _console->print(i);
            _console->println(" (might not exist or be configurable)");
        }
    }

    if (!targetChannelEnabled)
    {
        _console->print("Radio: ERROR - Failed to enable target channel ");
        _console->println(channelId);
        return false;
    }

    _console->println("Radio: Channel configuration completed");
    return true;
}

bool Sodaq_RN2483_Radio::setChannelFrequency(uint8_t channelId, uint32_t frequencyHz)
{
    char command[64];
    char response[16];

    sprintf(command, "mac set ch freq %u %lu", channelId, frequencyHz);
    return sendCommand(command, response, sizeof(response));
}

bool Sodaq_RN2483_Radio::setChannelDataRateRange(uint8_t channelId, uint8_t minDR, uint8_t maxDR)
{
    char command[64];
    char response[16];

    sprintf(command, "mac set ch drrange %u %u %u", channelId, minDR, maxDR);
    return sendCommand(command, response, sizeof(response));
}

bool Sodaq_RN2483_Radio::setChannelStatus(uint8_t channelId, bool enabled)
{
    char command[64];
    char response[16];

    sprintf(command, "mac set ch status %u %s", channelId, enabled ? "on" : "off");
    return sendCommand(command, response, sizeof(response));
}

bool Sodaq_RN2483_Radio::saveConfiguration()
{
    char response[16];

    _console->println("Radio: Saving MAC configuration to EEPROM");
    return sendCommand("mac save", response, sizeof(response));
}

bool Sodaq_RN2483_Radio::verifyChannelConfiguration(uint8_t channelId)
{
    char response[32];
    char command[32];

    _console->print("Radio: Verifying channel ");
    _console->print(channelId);
    _console->println(" configuration");

    // Check channel status
    sprintf(command, "mac get ch status %u", channelId);
    if (sendCommand(command, response, sizeof(response)))
    {
        _console->print("Radio: Channel ");
        _console->print(channelId);
        _console->print(" status: ");
        _console->println(response);
    }

    // Check channel frequency
    sprintf(command, "mac get ch freq %u", channelId);
    if (sendCommand(command, response, sizeof(response)))
    {
        _console->print("Radio: Channel ");
        _console->print(channelId);
        _console->print(" frequency: ");
        _console->println(response);
    }

    return true;
}

bool Sodaq_RN2483_Radio::sendCommand(const char *command, char *response, size_t responseSize, unsigned long timeout)
{
    flushInput();

    _console->print("Radio: Sending: ");
    _console->println(command);

    _loraStream->print(command);
    _loraStream->print("\r\n");

    if (response && responseSize > 0)
    {
        if (readLine(response, responseSize, timeout))
        {
            _console->print("Radio: Response: ");
            _console->println(response);
            return (strcmp(response, "ok") == 0);
        }
    }

    return true;
}

bool Sodaq_RN2483_Radio::readLine(char *buffer, size_t size, unsigned long timeout)
{
    size_t index = 0;
    unsigned long startTime = millis();
    bool inCR = false;

    memset(buffer, 0, size);

    while ((millis() - startTime) < timeout && index < size - 1)
    {
        if (_loraStream->available())
        {
            char c = _loraStream->read();

            if (c == '\r')
            {
                inCR = true;
                continue;
            }
            else if (c == '\n' && inCR)
            {
                break;
            }
            else
            {
                inCR = false;
            }

            buffer[index++] = c;
        }
        else
        {
            delay(1);
        }
    }

    buffer[index] = '\0';
    return index > 0;
}

void Sodaq_RN2483_Radio::flushInput()
{
    unsigned long startTime = millis();

    while (millis() - startTime < 100)
    {
        if (_loraStream->available())
        {
            _loraStream->read();
            startTime = millis();
        }
        else
        {
            delay(5);
            if (!_loraStream->available())
            {
                break;
            }
        }
    }
}