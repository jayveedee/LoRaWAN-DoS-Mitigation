#include "lib/Sodaq_RN2483/Sodaq_RN2483_internal.h"
#include "lib/Sodaq_RN2483/Sodaq_RN2483.h"
#include "lib/Sodaq_RN2483/Sodaq_RN2483.cpp"
#include "lib/Sodaq_RN2483/Utils.h"
#include <Arduino.h>

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

#define COMMAND_MODE 0 
#define LORA_MODE 1 

static const uint8_t APP_EUI[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01};
static const uint8_t APP_KEY[16] = {0xC8, 0x6D, 0xF0, 0xA1, 0x92, 0x34, 0xFA, 0x13, 0x3E, 0xD1, 0x6F, 0xAF, 0x08, 0xDB, 0x2D, 0x9B};

uint8_t count = 0;

// ---------------------------------------------------------------------------------------------------------
// Init Methods
// ---------------------------------------------------------------------------------------------------------
void setup() {
  while (!CONSOLE_STREAM && millis() < 10000);

  CONSOLE_STREAM.begin(LoRaBee.getDefaultBaudRate());
  LORA_STREAM.begin(LoRaBee.getDefaultBaudRate());

  CONSOLE_STREAM.println("------------------------------------");
  CONSOLE_STREAM.println("Booting...");

  if (FORCE_FULL_JOIN || !LoRaBee.initResume(LORA_STREAM, LORA_RESET_PIN)) {
    LoRaBee.init(LORA_STREAM, LORA_RESET_PIN, true, true);

    uint8_t eui[8];
    if (LoRaBee.getHWEUI(eui, sizeof(eui)) != 8) {
      return;
    }

    if (LoRaBee.initOTA(eui, APP_EUI, APP_KEY, false)) {
      CONSOLE_STREAM.println("OTAA Mode initialization successful.");
    } else {
      CONSOLE_STREAM.println("OTAA Mode initialization failed.");
      return;
    }
  }

  CONSOLE_STREAM.println("Done");
}

void loop() {
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
void fetchFrameCounters() {
  char dnbuf[16];
  char upbuf[16];

  LoRaBee.getMacParam("dnctr", dnbuf, 16);
  LoRaBee.getMacParam("upctr", upbuf, 16);

  CONSOLE_STREAM.print("Downlink frame counter: ");
  CONSOLE_STREAM.println(dnbuf);
  CONSOLE_STREAM.print("Uplink frame counter: ");
  CONSOLE_STREAM.println(upbuf);
}

void sendMessage() {
  uint8_t sf = 9;
  uint8_t frq = 1;
  uint8_t fsb = 0;
  char printbuf[64];  // Buffer to hold the formatted string
  sprintf(printbuf, "Initializing SF as %d, band rate as %d, channels as %d", sf, frq, fsb);
  CONSOLE_STREAM.println(printbuf);

  LoRaBee.setSpreadingFactor(sf); // Set spreading factor
  LoRaBee.setPowerIndex(frq); // Set band rate
  LoRaBee.setFsbChannels(fsb); // Enable all channels

  setRgbColor(0xFF, 0xFF, 0x00);

  uint8_t buf[] = {'t', 'e', 's', 't', count};
  CONSOLE_STREAM.print("Sending message... : ");
  for (int i = 0; i < sizeof(buf) - 1; i++) {  
    CONSOLE_STREAM.print((char)buf[i]);  
  }
  CONSOLE_STREAM.println(count);

  //uint8_t res = LoRaBee.send(LORA_PORT, buf, sizeof(buf));
  uint8_t res = LoRaBee.sendReqAck(LORA_PORT, buf, sizeof(buf), 3);

  CONSOLE_STREAM.print("LoRa transmission result: ");
  CONSOLE_STREAM.println(res);

  switch (res) {
  case NoError:
    CONSOLE_STREAM.println("Successful transmission.");
    setRgbColor(0x00, 0xFF, 0x00);
    if (count == 255) { count = 0; } 
    else { count++; } 
    delay(10000);
    break;
  case NoResponse:
    CONSOLE_STREAM.println("There was no response from the device.");
    setRgbColor(0xFF, 0x00, 0x00);
    break;
  case Timeout:
    CONSOLE_STREAM.println("Connection timed-out. Check your serial connection to the device! Sleeping for 20sec.");
    setRgbColor(0xFF, 0xA5, 0x00);
    delay(20000);
    break;
  case PayloadSizeError:
    CONSOLE_STREAM.println("The size of the payload is greater than allowed. Transmission failed!");
    setRgbColor(0xFF, 0x00, 0x00);
    delay(10000);
    break;
  case InternalError:
    CONSOLE_STREAM.println("Oh No! This shouldn't happen. Something is really wrong! Try restarting the device!\r\nThe program will now halt.");
    while (1) {
      setRgbColor(0xFF, 0xA5, 0x00);
      delay(250);
      setRgbColor(0xFF, 0x00, 0x00);
      delay(250);
    };
    break;
  case Busy:
    CONSOLE_STREAM.println("The device is busy. Sleeping for 10 extra seconds.");
    setRgbColor(0xFF, 0xA5, 0x00);
    delay(10000);
    break;
  case Silent:
    CONSOLE_STREAM.println("The device is silent. Sleeping for 10 extra seconds.");
    setRgbColor(0xFF, 0xA5, 0x00);
    delay(10000);
    break;
  case NoFreeChannel:
    CONSOLE_STREAM.println("The device has no free channel. Sleeping for 10 extra seconds.");
    setRgbColor(0xFF, 0xA5, 0x00);
    delay(10000);
    break;
  case NetworkFatalError:
    CONSOLE_STREAM.println("There is a non-recoverable error with the network connection. You should re-connect.\r\nThe program will now halt.");
    setRgbColor(0xFF, 0x00, 0x00);
    while (1) { };
    break;
  case NotConnected:
    CONSOLE_STREAM.println("The device is not connected to the network. Please connect to the network before attempting to send data.\r\nThe program will now halt.");
    setRgbColor(0xFF, 0x00, 0x00);
    while (1) { };
    break;
  case NoAcknowledgment:
    CONSOLE_STREAM.println("There was no acknowledgment sent back!");
    setRgbColor(0xFF, 0x00, 0x00);
    delay(10000);
    break;
  default:
    setRgbColor(0x00, 0x00, 0x00);
    break;
  }
}

void setRgbColor(uint8_t red, uint8_t green, uint8_t blue) {
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
  if (CONSOLE_STREAM.available()) {
    while (CONSOLE_STREAM.available()) {
      uint8_t inChar = CONSOLE_STREAM.read();
      LORA_STREAM.write(inChar);
    }
  }

  if (LORA_STREAM.available()) {
    while (LORA_STREAM.available()) {
      uint8_t inChar = LORA_STREAM.read();
      CONSOLE_STREAM.write(inChar);
    }
  }
}