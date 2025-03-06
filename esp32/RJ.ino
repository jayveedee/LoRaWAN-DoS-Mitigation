#include <RadioLib.h>

#define LORA_SCK        5
#define LORA_MISO       19
#define LORA_MOSI       27
#define LORA_SS         18
#define LORA_DIO0       26
#define LORA_DIO1       33
#define LORA_RST        14

float frequency =       867.1;

SX1276 radio = new Module(LORA_SS, LORA_DIO0, LORA_RST, LORA_DIO1);

void setup() {
  Serial.begin(115200);
  delay(2000);

  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);

  // Get SPI clock divider
  uint32_t clockDiv = SPI.getClockDivider();
    
    // ESP32 APB clock is 80 MHz, so SPI speed is:
  uint32_t spiSpeed = 80000000 / clockDiv;

  Serial.print("Estimated Default SPI Frequency: ");
  Serial.print(spiSpeed);
  Serial.println(" Hz");
  SPI.setFrequency(1000000);  // Lower SPI to 1 MHz
  
  // Setup SX1276 wiring to ESP32
  int state = radio.begin();
  if (state != RADIOLIB_ERR_NONE) {
    Serial.println("ERROR!!!!!!!");
    Serial.println(state);
    while (true);
  } 
  Serial.println("No errors so far");
  

  radio.setPreambleLength(8);
  radio.setOutputPower(14);
  radio.setCodingRate(5);
  radio.setSpreadingFactor(9);
  radio.setSyncWord(34);
  radio.setGain(1);

  delay(100);
  Serial.println("Setup done");
}

void loop() {
  radio.setFrequency(frequency);
  
  //*** Addition of printstatement for monitoring 
  int noise = radio.scanChannel();
  if (noise == RADIOLIB_PREAMBLE_DETECTED) {
    // radio.transmit("");
    Serial.println(noise);
    delay(100);
    Serial.println("Detected");
    Serial.println(frequency);
    Serial.print("RSSI: ");
    Serial.println(radio.getRSSI());

    Serial.print("SNR: ");
    Serial.println(radio.getSNR());
    while(true);
  }
  frequency = frequency + 0.2;
  if (frequency > 868.5) {
    frequency = 867.1;
  }

}
