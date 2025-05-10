// Include the aurduino library
#include <Arduino.h>

// Include the sodaq_RN2483 library for common utils
#include "lib/Sodaq_RN2483/Sodaq_RN2483_internal.h"
#include "lib/Sodaq_RN2483/Sodaq_RN2483.h"
#include "lib/Sodaq_RN2483/Sodaq_RN2483.cpp"
#include "lib/Sodaq_RN2483/Utils.h"

// Include all transmission strategies (have to include header and implementation)
#include "lib/strategies/TransmissionStrategy.h"
#include "lib/strategies/TransmissionStrategy.cpp"
#include "lib/strategies/StandardTransmission.h"
#include "lib/strategies/StandardTransmission.cpp"
#include "lib/strategies/RetryTransmission.h"
#include "lib/strategies/RetryTransmission.cpp"
#include "lib/strategies/DynamicTransmission.h"
#include "lib/strategies/DynamicTransmission.cpp"
#include "lib/strategies/LBTTransmission.h"
#include "lib/strategies/LBTTransmission.cpp"

// ---------------------------------------------------------------------------------------------------------
// Declarations
// ---------------------------------------------------------------------------------------------------------
#if defined(ARDUINO_SODAQ_EXPLORER)
#define CONSOLE_STREAM SerialUSB
#define LORA_STREAM Serial2
#define LORA_RESET_PIN LORA_RESET
#define BUTTON PUSH_BUTTON
#else
#error "Please select Sodaq ExpLoRer board"
#endif

#define COMMON_ANODE
#define FORCE_FULL_JOIN 1
#define LORA_PORT 1

// Transmission strategy types
#define STRATEGY_STANDARD 0 // No ACK, standard transmission
#define STRATEGY_RETRY 1    // With ACK and fixed retries
#define STRATEGY_DYNAMIC 2  // Dynamic spreading factor / coding rate / etc adjustment
#define STRATEGY_LBT 3      // Listen Before Talk jamming mitigation

// Set the active transmission strategy here
#define ACTIVE_TRANSMISSION_STRATEGY STRATEGY_LBT

static const uint8_t APP_EUI[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01};
static const uint8_t APP_KEY[16] = {0xC8, 0x6D, 0xF0, 0xA1, 0x92, 0x34, 0xFA, 0x13, 0x3E, 0xD1, 0x6F, 0xAF, 0x08, 0xDB, 0x2D, 0x9B};

uint8_t count = 0;

// Pointer to the active transmission strategy
TransmissionStrategy *activeStrategy = nullptr;

// ---------------------------------------------------------------------------------------------------------
// Init Methods
// ---------------------------------------------------------------------------------------------------------
void setup()
{
  // Wait for Serial to be available
  while (!CONSOLE_STREAM && millis() < 10000)
    ;

  CONSOLE_STREAM.begin(LoRaBee.getDefaultBaudRate());
  LORA_STREAM.begin(LoRaBee.getDefaultBaudRate());

  setRgbColor(0x00, 0xFF, 0x7F);

  CONSOLE_STREAM.println("------------------------------------");
  CONSOLE_STREAM.println("Booting...");

  if (FORCE_FULL_JOIN || !LoRaBee.initResume(LORA_STREAM, LORA_RESET_PIN))
  {
    LoRaBee.init(LORA_STREAM, LORA_RESET_PIN, true, true);

    uint8_t eui[8];
    if (LoRaBee.getHWEUI(eui, sizeof(eui)) != 8)
    {
      return;
    }

    if (LoRaBee.initOTA(eui, APP_EUI, APP_KEY, false))
    {
      CONSOLE_STREAM.println("OTAA Mode initialization successful.");
    }
    else
    {
      CONSOLE_STREAM.println("OTAA Mode initialization failed.");
      setRgbColor(0xFF, 0x00, 0x00);
      return;
    }
  }

// Initialize the selected transmission strategy
#if ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_STANDARD
  activeStrategy = new StandardTransmission(&CONSOLE_STREAM, &LoRaBee, setRgbColor);
  CONSOLE_STREAM.println("Standard transmission strategy initialized");
#elif ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_RETRY
  activeStrategy = new RetryTransmission(&CONSOLE_STREAM, &LoRaBee, setRgbColor, 3);
  CONSOLE_STREAM.println("Retry transmission strategy initialized");
#elif ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_DYNAMIC
  activeStrategy = new DynamicTransmission(&CONSOLE_STREAM, &LoRaBee, setRgbColor);
  CONSOLE_STREAM.println("Dynamic SF transmission strategy initialized");
#elif ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_LBT
  activeStrategy = new LBTTransmission(&CONSOLE_STREAM, &LoRaBee, setRgbColor);
  CONSOLE_STREAM.println("LBTTransmission strategy initialized");
#else
  // Default to standard transmission if no valid strategy is selected
  activeStrategy = new StandardTransmission(&CONSOLE_STREAM, &LoRaBee, setRgbColor);
  CONSOLE_STREAM.println("Default to standard transmission strategy");
#endif

  setRgbColor(0x00, 0xFF, 0x00);
  CONSOLE_STREAM.println("Done");

  delay(500);

  setRgbColor(0x00, 0x7F, 0xFF);
}

void loop()
{
  CONSOLE_STREAM.println("------------------------------------");

  // Prepare message data
  uint8_t buf[] = {'t', 'e', 's', 't', count};

  // Get frame counters for debugging
  activeStrategy->fetchFrameCounters();

  // Send using the active transmission strategy
  bool success = activeStrategy->sendMessage(LORA_PORT, buf, sizeof(buf), count);

// Additional actions for specific strategies
#if ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_LBT
  // Cast to LBTTransmission to access LBT-specific methods
  LBTTransmission *lbtStrategy = static_cast<LBTTransmission *>(activeStrategy);
  lbtStrategy->logJammingEvent();
#endif

  // No need to add transmission delay because the transmission strategies handle delays based on error states
}

// RGB LED control function
void setRgbColor(uint8_t red, uint8_t green, uint8_t blue)
{
#ifdef COMMON_ANODE
  red = 255 - red;
  green = 255 - green;
  blue = 255 - blue;
#endif
  analogWrite(LED_RED, red);
  analogWrite(LED_GREEN, green);
  analogWrite(LED_BLUE, blue);
}