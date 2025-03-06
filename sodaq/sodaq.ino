#include "Sodaq_RN2483.h"
#include <Arduino.h>

// ---------------------------------------------------------------------------------------------------------
// Declarations
// ---------------------------------------------------------------------------------------------------------
#if defined(ARDUINO_SODAQ_EXPLORER)
  #define CONSOLE_STREAM SerialUSB
  #define LORA_STREAM Serial2
  #define LORA_RESET_PIN LORA_RESET
#else
  #error "Please select Sodaq ExpLoRer board"
#endif

#define COMMON_ANODE
#define FORCE_FULL_JOIN 1
#define LORA_PORT 1

#define USE_OTAA 0
#define USE_ABP 1

#define COMMAND_MODE 0 
#define LORA_MODE 1 

#if USE_ABP
  static const uint8_t DEV_ADDR[4] = {0x01, 0x82, 0x29, 0xCC};
  static const uint8_t NWK_SKEY[16] = {0x25, 0x41, 0xB4, 0xA7, 0x14, 0x59, 0x35, 0x92, 0x73, 0x93, 0x35, 0x86, 0x17, 0x65, 0x1B, 0xCC};
  static const uint8_t APP_SKEY[16] = {0xBF, 0xF2, 0xCA, 0x2C, 0x71, 0x91, 0xF8, 0x95, 0x36, 0x5C, 0xCF, 0x82, 0x2C, 0x32, 0x24, 0xCC};
#elif USE_OTAA
  static const uint8_t APP_EUI[8] = {0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x06, 0xEB, 0x56};
  static const uint8_t APP_KEY[16] = {0xC8, 0x6D, 0xF0, 0xA1, 0x92, 0x34, 0xFA, 0x13, 0x3E, 0xD1, 0x6F, 0xAF, 0x08, 0xDB, 0x2D, 0x9B};
#else
  #error "Please use ABP or OTAA"
#endif

// ---------------------------------------------------------------------------------------------------------
// Init Methods
// ---------------------------------------------------------------------------------------------------------
void setup()
{
  while (!CONSOLE_STREAM && millis() < 10000);

  CONSOLE_STREAM.begin(LoRaBee.getDefaultBaudRate());
  LORA_STREAM.begin(LoRaBee.getDefaultBaudRate());
  //LoRaBee.setDiag(CONSOLE_STREAM);

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

    #if USE_ABP
      if (LoRaBee.initABP(DEV_ADDR, APP_SKEY, NWK_SKEY, false))
      {
        CONSOLE_STREAM.println("ABP Mode initialization successful.");
      }
      else
      {
        CONSOLE_STREAM.println("ABP Mode initialization failed.");
        return;
      }
    #else
      if (LoRaBee.initOTA(eui, APP_EUI, APP_KEY, false))
      {
        CONSOLE_STREAM.println("OTAA Mode initialization successful.");
      }
      else
      {
        CONSOLE_STREAM.println("OTAA Mode initialization failed.");
        return;
      }
    #endif
  }
  CONSOLE_STREAM.println("Done");
}

void loop()
{
  #if LORA_MODE
    CONSOLE_STREAM.println("------------------------------------");
    // get frame counters
    fetchFrameCounters();
    // send message
    sendMessage();
  #elif COMMAND_MODE
    // listen for ocmmands
    listenForCommands();
  #endif
}

// ---------------------------------------------------------------------------------------------------------
// Helper Methods
// ---------------------------------------------------------------------------------------------------------
void fetchFrameCounters()
{
  char dnbuf[16];
  char upbuf[16];

  LoRaBee.getMacParam("dnctr", dnbuf, 16);
  LoRaBee.getMacParam("upctr", upbuf, 16);

  CONSOLE_STREAM.print("Downlink frame counter: ");
  CONSOLE_STREAM.println(dnbuf);
  CONSOLE_STREAM.print("Uplink frame counter: ");
  CONSOLE_STREAM.println(upbuf);
}

void sendMessage()
{
  uint8_t sf = 9;
  uint8_t frq = 1;
  uint8_t fsb = 0;
  char printbuf[64];  // Buffer to hold the formatted string
  sprintf(printbuf, "Initializing SF as %d, band rate as %d, channels as %d", sf, frq, fsb);
  CONSOLE_STREAM.println(printbuf);

  LoRaBee.setSpreadingFactor(sf); // Set spreading factor
  LoRaBee.setPowerIndex(frq); // Set band rate
  LoRaBee.setFsbChannels(fsb); // Enable all channels

  // delay(3000);

  CONSOLE_STREAM.println("Sending message...");

  uint8_t buf[] = {'t', 'e', 's', 't'};

  uint8_t res = LoRaBee.send(LORA_PORT, buf, sizeof(buf));

  CONSOLE_STREAM.print("LoRa transmission result: ");
  CONSOLE_STREAM.println(res);

  switch (res)
  {
  case NoError:
    CONSOLE_STREAM.println("Successful transmission.");
    setRgbColor(0x00, 0xFF, 0x00);
    delay(10000);
    setRgbColor(0x00, 0x00, 0x00);
    break;
  case NoResponse:
    CONSOLE_STREAM.println("There was no response from the device.");
    setRgbColor(0xFF, 0x00, 0x00);
    break;
  case Timeout:
    CONSOLE_STREAM.println("Connection timed-out. Check your serial connection to the device! Sleeping for 20sec.");
    setRgbColor(0xFF, 0x00, 0x00);
    delay(20000);
    break;
  case PayloadSizeError:
    CONSOLE_STREAM.println("The size of the payload is greater than allowed. Transmission failed!");
    setRgbColor(0xFF, 0x00, 0x00);
    break;
  case InternalError:
    CONSOLE_STREAM.println("Oh No! This shouldn't happen. Something is really wrong! Try restarting the device!\r\nThe program will now halt.");
    setRgbColor(0xFF, 0x00, 0x00);
    while (1)
    {
      delay(250);
      setRgbColor(0x00, 0x00, 0x00);
      delay(250);
      setRgbColor(0xFF, 0x00, 0x00);
    };
    break;
  case Busy:
    CONSOLE_STREAM.println("The device is busy. Sleeping for 10 extra seconds.");
    delay(10000);
    break;
  case Silent:
    CONSOLE_STREAM.println("The device is silent. Sleeping for 10 extra seconds.");
    delay(10000);
    break;
  case NoFreeChannel:
    CONSOLE_STREAM.println("The device has no free channel. Sleeping for 10 extra seconds.");
    delay(10000);
    break;
  case NetworkFatalError:
    CONSOLE_STREAM.println("There is a non-recoverable error with the network connection. You should re-connect.\r\nThe program will now halt.");
    setRgbColor(0xFF, 0x00, 0x00);
    while (1)
    {
    };
    break;
  case NotConnected:
    CONSOLE_STREAM.println("The device is not connected to the network. Please connect to the network before attempting to send data.\r\nThe program will now halt.");
    setRgbColor(0xFF, 0x00, 0x00);
    while (1)
    {
    };
    break;
  case NoAcknowledgment:
    CONSOLE_STREAM.println("There was no acknowledgment sent back!");
    setRgbColor(0xFF, 0x00, 0x00);
    break;
  default:
    break;
  }
}

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

void listenForCommands() {
  if (CONSOLE_STREAM.available())
  {
    while (CONSOLE_STREAM.available()) 
    {
      uint8_t inChar = CONSOLE_STREAM.read();
      LORA_STREAM.write(inChar);
    }
  }

  if (LORA_STREAM.available())
  {
    while (LORA_STREAM.available()) 
    {
      uint8_t inChar = LORA_STREAM.read();
      CONSOLE_STREAM.write(inChar);
    }
  }
}