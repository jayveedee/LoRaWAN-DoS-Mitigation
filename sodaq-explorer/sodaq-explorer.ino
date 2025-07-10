// Include the aurduino libraries
#include <Arduino.h>

// Include the sodaq_RN2483 library for common utils
#include "lib/Sodaq_RN2483/Sodaq_RN2483_internal.h"
#include "lib/Sodaq_RN2483/Sodaq_RN2483.h"
#include "lib/Sodaq_RN2483/Sodaq_RN2483.cpp"
#include "lib/Sodaq_RN2483/Utils.h"

// Include custom made sodaq_RN2483 library for common radio commands
#include "lib/Sodaq_RN2483_Radio/Sodaq_RN2483_Radio.h"
#include "lib/Sodaq_RN2483_Radio/Sodaq_RN2483_Radio.cpp"

// Include all transmission strategies (have to include header and implementation)
#include "lib/Strategies/BaseStrategy.h"
#include "lib/Strategies/BaseStrategy.cpp"
#include "lib/Strategies/Standard/Standard.h"
#include "lib/Strategies/Standard/Standard.cpp"
#include "lib/Strategies/Retry/Retry.h"
#include "lib/Strategies/Retry/Retry.cpp"
#include "lib/Strategies/Dynamic/BaseDynamic.h"
#include "lib/Strategies/Dynamic/BaseDynamic.cpp"
#include "lib/Strategies/Dynamic/DynamicCR.h"
#include "lib/Strategies/Dynamic/DynamicCR.cpp"
#include "lib/Strategies/Dynamic/DynamicSF.h"
#include "lib/Strategies/Dynamic/DynamicSF.cpp"
#include "lib/Strategies/Dynamic/DynamicRetry.h"
#include "lib/Strategies/ListenBeforeTalk/LBT.h"
#include "lib/Strategies/ListenBeforeTalk/LBT.cpp"

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
#define STRATEGY_STANDARD 0         // No ACK, standard transmission
#define STRATEGY_RETRY 1            // With ACK and fixed retries
#define STRATEGY_DYNAMIC_SF 2       // Dynamic spreading factor adjustment
#define STRATEGY_DYNAMIC_CR 3       // Dynamic coding rate adjustment                     (cr does not work)
#define STRATEGY_DYNAMIC_SF_RETRY 4 // Dynamic spreading adjustment with 3 retries
#define STRATEGY_DYNAMIC_CR_RETRY 5 // Dynamic coding rate adjustment with 3 retries      (cr does not work)
#define STRATEGY_LBT 6              // Listen Before Talk jamming mitigation              (lbt does not work)

// Set the active transmission strategy here
#define ACTIVE_TRANSMISSION_STRATEGY STRATEGY_STANDARD

static const uint8_t APP_EUI[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01};
static const uint8_t APP_KEY[16] = {0xC8, 0x6D, 0xF0, 0xA1, 0x92, 0x34, 0xFA, 0x13, 0x3E, 0xD1, 0x6F, 0xAF, 0x08, 0xDB, 0x2D, 0x9B};

uint8_t count = 0;

// Pointer to the active transmission strategy
BaseStrategy *activeStrategy = nullptr;

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
  factoryReset();

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
  activeStrategy = new Standard(&CONSOLE_STREAM, &LORA_STREAM, &LoRaBee, setRgbColor);
  CONSOLE_STREAM.println("Standard transmission strategy initialized");
#elif ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_RETRY
  activeStrategy = new Retry(&CONSOLE_STREAM, &LORA_STREAM, &LoRaBee, setRgbColor, 3);
  CONSOLE_STREAM.println("Retry transmission strategy initialized");
#elif ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_DYNAMIC_SF
  activeStrategy = new DynamicSF(&CONSOLE_STREAM, &LORA_STREAM, &LoRaBee, setRgbColor);
  CONSOLE_STREAM.println("Dynamic SF transmission strategy initialized");
#elif ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_DYNAMIC_CR
  activeStrategy = new DynamicCR(&CONSOLE_STREAM, &LORA_STREAM, &LoRaBee, setRgbColor);
  CONSOLE_STREAM.println("Dynamic CR transmission strategy initialized");
#elif ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_DYNAMIC_SF_RETRY
  activeStrategy = new DynamicRetrySF(&CONSOLE_STREAM, &LORA_STREAM, &LoRaBee, setRgbColor);
  CONSOLE_STREAM.println("Dynamic SF Retry transmission strategy initialized");
#elif ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_DYNAMIC_CR_ReTRY
  activeStrategy = new DynamicRetryCR(&CONSOLE_STREAM, &LORA_STREAM, &LoRaBee, setRgbColor);
  CONSOLE_STREAM.println("Dynamic CR Retry transmission strategy initialized");
#elif ACTIVE_TRANSMISSION_STRATEGY == STRATEGY_LBT
  activeStrategy = new LBT(&CONSOLE_STREAM, &LORA_STREAM, &LoRaBee, setRgbColor);
  CONSOLE_STREAM.println("LBTTransmission strategy initialized");
#else
  // Default to standard transmission if no valid strategy is selected
  activeStrategy = new Standard(&CONSOLE_STREAM, &LORA_STREAM, &LoRaBee, setRgbColor);
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
  uint8_t buf[] = {'t', 'e', 's', 't', count}; // 5 bytes of data

  // Get frame counters for debugging
  FrameCounters counters = activeStrategy->fetchFrameCounters();

  // Send using the active transmission strategy
  bool success = activeStrategy->sendMessage(LORA_PORT, buf, sizeof(buf), count);

  if (counters.uplink >= 49)
  {
    activeStrategy->printTransmissionCounters();
    CONSOLE_STREAM.println("Reached 50 uplink frame counters, halting Sodaq.");
    while (1)
      ;
  }

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

// Only use if device is in unrecoverable state after messing with radio commands
void factoryReset()
{
  CONSOLE_STREAM.println("Sending system reset command...");
  LORA_STREAM.println("sys factoryRESET");

  // Wait for reset to complete
  delay(1000);

  // Read and print the response from the module
  CONSOLE_STREAM.println("Response from module:");
  unsigned long startTime = millis();
  while (millis() - startTime < 3000)
  {
    if (LORA_STREAM.available())
    {
      char c = LORA_STREAM.read();
      CONSOLE_STREAM.write(c);
    }
  }

  CONSOLE_STREAM.println("\nReset completed.");
  delay(2000);
}