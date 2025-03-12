#include <RadioLib.h>

#define LORA_SCK        5
#define LORA_MISO       19
#define LORA_MOSI       27
#define LORA_SS         18
#define LORA_DIO0       26
#define LORA_DIO1       33
#define LORA_RST        14

#define MAX_PAYLOAD_SIZE 255

float frequency =       867.1;

SX1276 radio = new Module(LORA_SS, LORA_DIO0, LORA_RST, LORA_DIO1);

void setup() {
  while (!Serial && millis() < 10000);

  Serial.begin(115200);
  delay(2000);

  Serial.println("------------------------------------");
  Serial.println("Booting...");

  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);

  uint32_t clockDiv = SPI.getClockDivider(); // Get SPI clock divider
  uint32_t spiSpeed = 80000000 / clockDiv; // ESP32 APB clock is 80 MHz, so SPI speed is:

  Serial.print("Estimated Default SPI Frequency: ");
  Serial.print(spiSpeed);
  Serial.println(" Hz");
  SPI.setFrequency(1000000);  // Lower SPI to 1 MHz
  
  int state = radio.begin();
  if (state != RADIOLIB_ERR_NONE) {
    Serial.print("Error. State: ");
    Serial.println(state);
    while (true);
  } 

  radio.setPreambleLength(8);
  radio.setOutputPower(14);
  radio.setBandwidth(125.0);
  radio.setCodingRate(5);
  radio.setSpreadingFactor(9);
  radio.setSyncWord(34);
  radio.setGain(1);

  delay(100);
  Serial.println("Setup done");
}

void loop() {
  radio.setFrequency(frequency);
  int noise = radio.scanChannel();

  if (noise == RADIOLIB_PREAMBLE_DETECTED) {
    Serial.println("------------------------------------");
    Serial.print("LoRa Preamble Detected! The frequency is: ");
    Serial.println(frequency);

    // radio.transmit("");

    int state = fetchPacket(true);

    if (state == RADIOLIB_ERR_NONE) {
      Serial.println("No error.");
    } else {
      Serial.println("Error.");
    }

    radio.standby();
  }

  frequency = frequency + 0.2;
  if (frequency > 868.7) {
    frequency = 867.1;
  }
}

int16_t fetchPacket(bool printBytes) {
  Serial.println("Receiving LoRa packet...");

  int16_t state;
  int numBytes = radio.getPacketLength();

  if (printBytes) {
    byte byteArr[numBytes];  
    state = radio.readData(byteArr, numBytes);

    Serial.print("  Data (Hex): ");
    for (int i = 0; i < numBytes; i++) {
      Serial.printf("%02X ", byteArr[i]);  
    }
    Serial.println();
  } else {
    String str;
    state = radio.readData(str);

    Serial.print("  Data (String): ");
    Serial.println(str);
  }

  Serial.print("  State: ");
  Serial.println(state);

  Serial.println("Packet Received.");

  return state;
}

void parseByteArray(const uint8_t* data, size_t length) {
  Serial.print("Length of bytes: ");
  Serial.println(length);
  if (length < 12) {
      Serial.println("Error: Data too small to extract required fields.");
      return;
  }

  // Convert first 4 bytes to float
  float num1;
  memcpy(&num1, data, sizeof(float));

  // Convert next 4 bytes to float
  float num2;
  memcpy(&num2, data + 4, sizeof(float));

  // Convert next 4 bytes to ASCII string (since it's stored as bytes)
  char text[5] = {}; // 4 characters + null terminator
  memcpy(text, data + 8, 4);

  // Convert remaining bytes to integer
  int number = 0;
  if (length > 12) {
      memcpy(&number, data + 12, sizeof(int));
  }

  // Print extracted values using Serial
  Serial.print("Float 1: ");
  Serial.println(num1, 6);  // Print float with 6 decimal places

  Serial.print("Float 2: ");
  Serial.println(num2, 6);

  Serial.print("ASCII Text: ");
  Serial.println(text);  // Converts byte data into an ASCII string

  Serial.print("Integer: ");
  Serial.println(number);
}
