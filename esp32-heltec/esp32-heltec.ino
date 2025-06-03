#include "LoRaWan_APP.h"
#include "Arduino.h"

static RadioEvents_t RadioEvents;

void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println("Initializing SX1262 LoRa...");

  // Attach empty callbacks (or real ones if needed)
  RadioEvents.TxDone = NULL;
  RadioEvents.RxDone = NULL;
  RadioEvents.TxTimeout = NULL;
  RadioEvents.RxTimeout = NULL;
  RadioEvents.RxError = NULL;

  Radio.Init(&RadioEvents);  // ✅ fix: pass pointer to RadioEvents

  Radio.SetChannel(868000000);  // Set frequency (Europe)

  // Configure TX parameters
  Radio.SetTxConfig(
    MODEM_LORA,
    14,     // TX power
    0,      // Freq deviation (unused)
    0,      // Bandwidth (0 = 125kHz)
    7,      // SF7
    1,      // Coding rate 4/5
    8,      // Preamble length
    false,  // Fixed length
    true,   // CRC
    0,      // Frequency hopping
    0,      // Hop period
    false,  // IQ inversion
    3000    // Timeout
  );

  Serial.println("LoRa ready. Sending packets...");
}

void loop() {
  uint8_t payload[] = "Hello from Heltec SX1262";
  Radio.Send(payload, sizeof(payload));
  Serial.println("Packet sent!");

  delay(5000);
}
