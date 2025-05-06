#include <RadioLib.h>

#define LORA_SCK        05
#define LORA_MISO       19
#define LORA_MOSI       27
#define LORA_SS         18
#define LORA_DIO0       26
#define LORA_DIO1       33
#define LORA_RST        14

float frequency =       867.1;
int SF = 9;

SX1276 radio = new Module(LORA_SS, LORA_DIO0, LORA_RST, LORA_DIO1);

void setup() {
  Serial.begin(115200);
  delay(2000);
  // Setup SX1276 wiring to ESP32
  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);

  // Get SPI clock divider
  uint32_t clockDiv = SPI.getClockDivider();
    
    // ESP32 APB clock is 80 MHz, so SPI speed is:
  uint32_t spiSpeed = 80000000 / clockDiv;

  Serial.print("Estimated Default SPI Frequency: ");
  Serial.print(spiSpeed);
  Serial.println(" Hz");
  SPI.setFrequency(1000000);  // Lower SPI to 1 MHz


  int state = radio.begin();
  if (state != RADIOLIB_ERR_NONE) {
    while (true);
  } 
  

  radio.setPreambleLength(8);
  radio.setOutputPower(17);
  radio.setBandwidth(125.0);
  radio.setCodingRate(5);
  radio.setSpreadingFactor(SF);
  radio.setSyncWord(34);
  radio.setGain(1);

  delay(100);
}

void loop() {
  radio.setFrequency(frequency);
  //*** Addition of printstatement for monitoring 
  if (radio.scanChannel() == RADIOLIB_PREAMBLE_DETECTED) {
    delay(1000);
    Serial.println("Preamble detected");
    Serial.println(frequency);
    Serial.print("SF: ");
    Serial.println(SF);
    byte dummy[60] = {0};  // Longer payload → longer airtime
    radio.transmit(dummy, sizeof(dummy));

    // radio.transmit("");
    delay(100);
    Serial.println("radio transmitting");
    Serial.println("__________________");
  }
  frequency = frequency + 0.2;
  if (frequency > 868.5) {
    SF++;
    if (SF > 12) {
      SF = 9;
    }
    radio.setSpreadingFactor(SF);
    frequency = 867.1;
  }

}
