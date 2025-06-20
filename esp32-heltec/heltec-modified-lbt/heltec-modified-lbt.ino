#include <LoRaWan_APP.h>

/* OTAA para*/
uint8_t devEui[] = {0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x07, 0x13, 0x09};
uint8_t appEui[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02};
uint8_t appKey[] = {0x7E, 0xAB, 0x4C, 0x95, 0xCF, 0x55, 0xAB, 0xE5,
                    0xDF, 0x81, 0x27, 0xCF, 0x6D, 0x0A, 0xD6, 0x18};

/* ABP para*/
uint8_t nwkSKey[] = {0};
uint8_t appSKey[] = {0};
uint32_t devAddr = 0;

/*LoraWan channelsmask, default channels 0-7*/
uint16_t userChannelsMask[6] = {0x00FF, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000};

/*LoraWan region, select in arduino IDE tools*/
LoRaMacRegion_t loraWanRegion = LORAMAC_REGION_EU868;

/*LoraWan Class, Class A and Class C are supported*/
DeviceClass_t loraWanClass = CLASS_A;

/*the application data transmission duty cycle.  value in [ms].*/
uint32_t appTxDutyCycle = 15000;

/*OTAA or ABP*/
bool overTheAirActivation = true;

/*ADR enable*/
// bool loraWanAdr = true;
bool loraWanAdr = false;

/* Indicates if the node is sending confirmed or unconfirmed messages */
bool isTxConfirmed = false;

/* Application port */
uint8_t appPort = 2;
/*!
 * Number of trials to transmit the frame, if the LoRaMAC layer did not
 * receive an acknowledgment. The MAC performs a datarate adaptation,
 * according to the LoRaWAN Specification V1.0.2, chapter 18.4, according
 * to the following table:
 *
 * Transmission nb | Data Rate
 * ----------------|-----------
 * 1 (first)       | DR
 * 2               | DR
 * 3               | max(DR-1,0)
 * 4               | max(DR-1,0)
 * 5               | max(DR-2,0)
 * 6               | max(DR-2,0)
 * 7               | max(DR-3,0)
 * 8               | max(DR-3,0)
 *
 * Note, that if NbTrials is set to 1 or 2, the MAC will not decrease
 * the datarate, in case the LoRaMAC layer did not receive an acknowledgment
 */
uint8_t confirmedNbTrials = 4;

RTC_DATA_ATTR uint8_t probeCounter = 0;
RTC_DATA_ATTR uint8_t probeCounterByFrame[51] = {0};  // Index = Frame counter, Value = probeCounter

uint32_t eu868Frequencies[] = {
    868100000, 868300000, 868500000,
    867100000, 867300000, 867500000,
    867700000, 867900000};

/* Prepare real data */
static void prepareTxFrame(uint8_t port)
{
  appDataSize = 5;
  appData[0] = 't';
  appData[1] = 'e';
  appData[2] = 's';
  appData[3] = 't';
  appData[4] = getUplinkFrameCounter();
}

/* Send a meaningless probe packet to bait a reactive jammer */
void sendProbePacket(uint32_t frequencyHz)
{
  Radio.Sleep(); // Reset state

  Radio.SetChannel(frequencyHz);

  Radio.SetTxConfig(
      MODEM_LORA, // Use LoRa modulation
      14,         // Power: +14 dBm (adjust as needed)
      0,          // Frequency deviation: 0 (not used in LoRa)
      0,          // Bandwidth: 0 = 125 kHz
      9,          // Datarate: SF9 (512 chips/symbol)
      1,          // Coding rate: 1 = 4/5
      12,         // Preamble length: 12 symbols (longer preamble = better jammer detection)
      false,      // Variable length packet (not fixed)
      true,       // Enable CRC (optional, jammers don’t care)
      false,      // No frequency hopping
      0,          // Hop period (not used)
      false,      // No IQ inversion (standard uplinks = false; can use true to *avoid* decoding)
      3000        // Timeout in milliseconds
  );

  uint8_t dummyPayload[1] = {0x42};               // meaningless data
  Radio.Send(dummyPayload, sizeof(dummyPayload)); // ⬅️ Raw radio transmit

  Serial.println("🧪 Raw probe LoRa packet sent.");
  delay(50); // Optional: allow TX to complete before switching to RX
  probeCounter++;
}

/* Check RSSI and SNR after baiting */
bool isLikelyJammed(uint32_t frequencyHz)
{
  Radio.Sleep();
  Radio.SetChannel(frequencyHz);
  Radio.Rx(0);  // Continuous RX mode

  delay(200); // Allow time for potential jammer to react

  int16_t rssi;
  int8_t snr;
  getSnrRssi(&rssi, &snr);

  Radio.Sleep();

  Serial.printf("📡 RSSI: %d dBm, SNR: %d dB\n", rssi, snr);

  // Custom jamming heuristic
  return (rssi > -85 && snr < -7);
}


void setup()
{
  Serial.begin(115200);
  randomSeed(analogRead(A0));
  Mcu.begin(HELTEC_BOARD, SLOW_CLK_TPYE);
}

void loop()
{
  switch (deviceState)
  {
  case DEVICE_STATE_INIT:
  {
    #if (LORAWAN_DEVEUI_AUTO)
      LoRaWAN.generateDeveuiByChipID();
    #endif
    LoRaWAN.init(loraWanClass, loraWanRegion);
    LoRaWAN.setDefaultDR(3); // 3 == SF9, 2 == SF10, 1 == SF11, 0 == SF12
    break;
  }
  case DEVICE_STATE_JOIN:
  {
    LoRaWAN.join();
    // After OTAA join, remove all default channels (0-7)
    for (int i = 0; i <= 7; i++) {
        LoRaMacChannelRemove(i);
    }

    break;
  }
  case DEVICE_STATE_SEND:
  {
    bool sent = false;

    shuffleFrequencies(eu868Frequencies, sizeof(eu868Frequencies) / sizeof(eu868Frequencies[0]));

    for (uint8_t i = 0; i < sizeof(eu868Frequencies) / sizeof(eu868Frequencies[0]); i++)
    {
      uint32_t freq = eu868Frequencies[i];

      Serial.printf("Trying %.1f MHz...\n", freq / 1e6);
      sendProbePacket(freq);

      if (!isLikelyJammed(freq))
      {
        prepareTxFrame(appPort);
        setTxFrequency(freq);
        uint32_t fcnt = getUplinkFrameCounter();
        LoRaWAN.send();

        // Save probeCounter at index fcnt
        if (fcnt < 51) {
          probeCounterByFrame[fcnt] = probeCounter;
        }

        Serial.printf("📤 Transmitting on %.1f MHz | Count: %d\n", freq / 1e6, getUplinkFrameCounter());
        probeCounter = 0;
        sent = true;
        break;
      }
      else
      {
        Serial.printf("🚫 Jammed (possibly): %.1f MHz\n", freq / 1e6);
      }
    }

    if (!sent)
    {
      Serial.println("All channels jammed. Skipping transmission.");
    }

    deviceState = DEVICE_STATE_CYCLE;
    break;
  }

  case DEVICE_STATE_CYCLE:
  {
    txDutyCycleTime = appTxDutyCycle + randr(-APP_TX_DUTYCYCLE_RND, APP_TX_DUTYCYCLE_RND);
    LoRaWAN.cycle(txDutyCycleTime);
    deviceState = DEVICE_STATE_SLEEP;
    break;
  }

  case DEVICE_STATE_SLEEP:
  {
    LoRaWAN.sleep(loraWanClass);
    break;
  }

  default:
  {
    deviceState = DEVICE_STATE_INIT;
    break;
  }
  }

  if (getUplinkFrameCounter() >= 51)
  {
    Serial.println("Reached 50 (actually 51) transmissions. Halting.");
    for (uint8_t i = 0; i < 51; i++) {
      Serial.printf("Frame %02d: %d probes\n", i, probeCounterByFrame[i]);
    }
    while (true)
      ;
  }
}

void shuffleFrequencies(uint32_t *freqs, size_t size)
{
  for (size_t i = size - 1; i > 0; i--)
  {
    size_t j = random(i + 1); // random(0, i)
    uint32_t temp = freqs[i];
    freqs[i] = freqs[j];
    freqs[j] = temp;
  }
}
void setTxFrequency(uint32_t frequency)
{
  ChannelParams_t customChannel;
  customChannel.Frequency = frequency;
  customChannel.Rx1Frequency = frequency;
  customChannel.DrRange.Value = (DR_5 << 4) | DR_0; // DR_0 to DR_5
  customChannel.Band = 0;

  // Use a custom, high index (above 8) to avoid clashing with TTN-managed channels
  const uint8_t customIndex = 8;
  LoRaMacChannelAdd(customIndex, customChannel);

  // Enable only your custom index
  memset(userChannelsMask, 0, sizeof(userChannelsMask));
  userChannelsMask[customIndex / 16] = (1 << (customIndex % 16));

  // Apply mask to runtime channels
  MibRequestConfirm_t mibReq;
  mibReq.Type = MIB_CHANNELS_MASK;
  mibReq.Param.ChannelsMask = userChannelsMask;
  LoRaMacMibSetRequestConfirm(&mibReq);

  // Apply mask to default channel set
  mibReq.Type = MIB_CHANNELS_DEFAULT_MASK;
  mibReq.Param.ChannelsMask = userChannelsMask;
  LoRaMacMibSetRequestConfirm(&mibReq);
}

void getSnrRssi(int16_t* rssiOut, int8_t* snrOut)
{
  PacketStatus_t pktStatus;
  SX126xGetPacketStatus(&pktStatus);
  *rssiOut = pktStatus.Params.LoRa.RssiPkt;
  *snrOut = pktStatus.Params.LoRa.SnrPkt;
}

uint32_t getUplinkFrameCounter() {
    MibRequestConfirm_t mib;
    mib.Type = MIB_UPLINK_COUNTER;
    LoRaMacMibGetRequestConfirm(&mib);
    return mib.Param.UpLinkCounter;
}