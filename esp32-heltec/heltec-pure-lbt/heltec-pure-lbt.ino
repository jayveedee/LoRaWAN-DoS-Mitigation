/* Heltec Automation LoRaWAN communication example
 *
 * Function:
 * 1. Upload node data to the server using the standard LoRaWAN protocol.
 *  
 * Description:
 * 1. Communicate using LoRaWAN protocol.
 * 
 * HelTec AutoMation, Chengdu, China
 * 成都惠利特自动化科技有限公司
 * www.heltec.org
 *
 * */

#include "../lib/CustomLoRa/LoRaWan_APP.h"

// #define HELTEC_BOARD 1
// #define SLOW_CLK_TYPE RTC_SLOW_CLK_RC



/* OTAA para*/
uint8_t devEui[] = { 0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x07, 0x13, 0x09 };
uint8_t appEui[]    = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02 };
uint8_t appKey[]    = { 0x7E, 0xAB, 0x4C, 0x95, 0xCF, 0x55, 0xAB, 0xE5,
                 0xDF, 0x81, 0x27, 0xCF, 0x6D, 0x0A, 0xD6, 0x18 };

/* ABP para*/
uint8_t nwkSKey[] = { 0 };
uint8_t appSKey[] = { 0 };
uint32_t devAddr =  0;

/*LoraWan channelsmask, default channels 0-7*/ 
uint16_t userChannelsMask[6]={ 0x00FF,0x0000,0x0000,0x0000,0x0000,0x0000 };

/*LoraWan region, select in arduino IDE tools*/
LoRaMacRegion_t loraWanRegion = LORAMAC_REGION_EU868;

/*LoraWan Class, Class A and Class C are supported*/
DeviceClass_t  loraWanClass = CLASS_A;

/*the application data transmission duty cycle.  value in [ms].*/
uint32_t appTxDutyCycle = 15000;

/*OTAA or ABP*/
bool overTheAirActivation = true;

/*ADR enable*/
// bool loraWanAdr = true;
bool loraWanAdr = false;

/* Indicates if the node is sending confirmed or unconfirmed messages */
bool isTxConfirmed = true;

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

uint32_t eu868Frequencies[] = {
  868100000, 868300000, 868500000,
  867100000, 867300000, 867500000,
  867700000, 867900000
};

RTC_DATA_ATTR uint8_t counter = 0;

/* Prepares the payload of the frame */
static void prepareTxFrame( uint8_t port, uint8_t count)
{
  /*appData size is LORAWAN_APP_DATA_MAX_SIZE which is defined in "commissioning.h".
  *appDataSize max value is LORAWAN_APP_DATA_MAX_SIZE.
  *if enabled AT, don't modify LORAWAN_APP_DATA_MAX_SIZE, it may cause system hanging or failure.
  *if disabled AT, LORAWAN_APP_DATA_MAX_SIZE can be modified, the max value is reference to lorawan region and SF.
  *for example, if use REGION_CN470, 
  *the max value for different DR can be found in MaxPayloadOfDatarateCN470 refer to DataratesCN470 and BandwidthsCN470 in "RegionCN470.h".
  */
    appDataSize = 5;
    appData[0] = 't';
    appData[1] = 'e';
    appData[2] = 's';
    appData[3] = 't';
    appData[4] = count;
}

bool isLikelyJammed(uint32_t frequencyHz) {
  Serial.printf("\U0001F50D Probing %.1f MHz for jamming...\n", frequencyHz / 1e6);

  Radio.Sleep();                     // ensure radio is idle
  Radio.SetChannel(frequencyHz);    // set channel
  Radio.Rx(0);                       // enable continuous RX mode
  delay(50);                         // short listen duration

  int16_t rssi = Radio.Rssi(MODEM_LORA);  // ✅ use RadioRssi()
  Radio.Sleep();

  Serial.printf("📶 RSSI: %d dBm\n", rssi);

  // Threshold can be tuned. Jammed if signal power is too strong
  return rssi > -85;
}

void setup() {
  Serial.begin(115200);
  Mcu.begin(HELTEC_BOARD,SLOW_CLK_TPYE);
}

void loop()
{
  switch( deviceState )
  {
    case DEVICE_STATE_INIT:
    {
        #if(LORAWAN_DEVEUI_AUTO)
            LoRaWAN.generateDeveuiByChipID();
        #endif
        LoRaWAN.init(loraWanClass,loraWanRegion);
        //both set join DR and DR when ADR off 
        LoRaWAN.setDefaultDR(5);
        break;
    }
    case DEVICE_STATE_JOIN:
    {
        LoRaWAN.join();
        break;
    }
    case DEVICE_STATE_SEND:
    {
        bool sent = false;

        for (uint8_t i = 0; i < sizeof(eu868Frequencies) / sizeof(eu868Frequencies[0]); i++) {
            uint32_t freq = eu868Frequencies[i];
            if (!isLikelyJammed(freq)) {
                prepareTxFrame(appPort, counter);
                Serial.printf("\u2705 Transmitting on %.1f MHz\n", freq / 1e6);
                LoRaWAN.setTxFrequency(freq); // You may need to implement this via MAC commands or lower-level modification
                LoRaWAN.send();
                sent = true;
                counter++;
                break;
            } else {
                Serial.printf("Channel %.1f MHz is jammed.\n", freq / 1e6);
            }
      }

      if (!sent) {
        Serial.println("\u274C All channels jammed. Skipping transmission.");
      }

        deviceState = DEVICE_STATE_CYCLE;
        break;
    }
    case DEVICE_STATE_CYCLE:
    {
        // Schedule next packet transmission
        txDutyCycleTime = appTxDutyCycle + randr( -APP_TX_DUTYCYCLE_RND, APP_TX_DUTYCYCLE_RND );
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
  if (counter > 49) {
    Serial.println("Reached 50 uplink frame counters, halting Heltec.");
    while (1);
  }
}
