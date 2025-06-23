# LoRaWAN-DoS-Mitigation

Master thesis project about LoRaWAN DoS Mitigation.

## Authors of the repository

- `Jákup Viljam Dam` `s185095` `Computer Science and Engineering`
- `Mohammad Tawrat Nafiu Uddin` `s184174` `Computer Science and Engineering`

## How it works

We are simulating a scenario in which a reactive jammer (implemented on an ESP32) attempts to disrupt the communication of a legitimate LoRa device at the physical (PHY) layer. The jammer continuously scans all channels for a LoRa preamble, and upon detection, immediately transmits a jamming signal to interfere with the ongoing transmission. This constitutes a denial-of-service (DoS) attack on the legitimate communication.

The primary goal of the project is not merely to demonstrate the attack, but to explore detection and mitigation strategies that can be implemented on the legitimate device. The intention is to make these strategies adaptable to various hardware platforms, including devices like the Sodaq ExpLoRer, ESP32-based LoRa modules, and potentially others.

When running the system, the setup involves an active jammer attempting to disrupt communication, while the legitimate device tries to detect the attack and respond through adaptive mechanisms that either avoid, withstand, or neutralize the interference.

## Installation

How to install and run the project

To run this setup, ensure the following requirements are met:

- A TTN (The Things Network) server must be properly configured, with support for OTAA (Over-The-Air Activation) for all participating devices.
- The following hardware and software components are required:

1. Lilygo T-Display ESP32 with SX1276 LoRa Chip
   - Required Arduino Libraries:
     - `LoRa` by Sandeep Mistry
     - `RadioLib` by Jan Gnomes
   - Board Manager:
     - `ESP32` by Espressif Systems
2. Sodaq ExpLoRer with RN2483 LoRa Module
   - Required Arduino Libraries:
     - `Sodaq_wdt` by GabrielNotman, SODAQ
   - Board Manager:
     - `SODAQ SAMD Boards` by SODAQ
3. Heltec WiFi LoRa 32(V3) ESP32 
    - Required Arduino Libraries:
      - `Heltec ESP32 Dev-Boards` by Heltec Automation
    - Board Manager:
      - `Heltec ESP32 Series Dev-Boards` by Heltec Automation
    - Required USB Driver:
      - [Guide for downloading and installing driver](https://docs.heltec.org/general/establish_serial_connection.html) from Heltec Docs
4. The Things Network (TTN)
   - Setup end-device formatters located in `ttn/heltecFormatter.js` and `ttn/sodaqFormatter.js`
      - [Guide for Creating Payload Formatter](https://www.thethingsindustries.com/docs/integrations/payload-formatters/create/) from TTN
   - Setup Webhook for the Flask Server
     - [Guide for Creating Webhooks](https://www.thethingsindustries.com/docs/integrations/webhooks/creating-webhooks/) from TTN
5. Dragino LPS8N LoRaWAN Gateway
   - Must be registered and connected to the TTN network using OTAA.

### Installation

1. Clone the Repo
   - SODAQ, Heltec, and Jammer
     1. Use the Arduino IDE and install the relevant libraries and board managers
     2. Connect your devices to your PC via USB
     3. Compile and flash the devices with the code provided
     4. When the code has been flashed, the devices should be up and running
   - Packet Monitor Server
     1. Install requirements.txt (recommended inside of a virtual environemnt)

## Usage

### SODAQ 
In the code for the legitimate devices and the jammer, there are some configuraitons that can be changed and reflashed onto the devices. For the Sodaq, it has the following:

```cpp
// Transmission strategy types
#define STRATEGY_STANDARD 0         // No ACK, standard transmission
#define STRATEGY_RETRY 1            // With ACK and fixed retries
#define STRATEGY_DYNAMIC_SF 2       // Dynamic spreading factor adjustment

// Set the active transmission strategy here
#define ACTIVE_TRANSMISSION_STRATEGY STRATEGY_STANDARD // swap out the STRATEGY_STANDARD
```

### Heltec
For the Heltec the only thing you need to do to change strategies is to flash the different .ino files onto the Heltec device. 

- For the LBT strategy, flash the file `heltec-pure-lbt/heltec-pure-lbt.ino`
- For the PALBT strategy, flash the file `heltec-modified-lbt/heltec-modified-lbt.ino`

### Jammer
The jammer has two modes, one that targets frequencies only and another that hops between spreading factors as well:

```cpp
// Jamming strategy types
#define STATIC_JAMMING 0 // Jams frequencies between 867.1 - 868.5 (EU863-870)
#define DYNAMIC_JAMMING 1 // Jams frequencies between 867.1 - 868.5 (EU863-870) and spreading factors 9 - 12

// Set the active jamming strategy here
#define JAMMING_STRATEGY STATIC_JAMMING // swap out the DEFAULT_JAMMING
```

### Packet Monitor Server
The packet monitor server listens for packets sent from TTN. When it has captured 50 messages from a single device it will save statistics of that device in the folder `packet-monitor-server/stats/<DEVEUI>` where DEVEUI is device specific. This file will keep updating as time goes on. It is also possible to call the endpoint `/save` which in turn will save a hardcoded device's window. This could be changed in the future and making it a `/POST` instead where you send a specific DEVEUI.

You run the server with the following command `python3 packet-monitor-server-py` or `python packet-monitor-server-py`

### Extra
In the directory `ttn/` some python files are used to calculate power usage (`calc.py`) plot statistics manually (`plot.py`) from `ttn/data/device-ttn-combined/stats.csv` and investigate logs (`stats.py`) gathered from TTN located in `ttn/data/logs`.

## Logging

When using the Arduino IDE's Serial Monitor, you can observe detailed information about jamming attempts as well as the detection and mitigation strategies being applied in real time. On the Sodaq device, LED indicators also provide a quick visual reference for various error states, making it easy to determine whether a transmission was successful or if interference occurred.

## Acknowledgements

This project draws inspiration from a previous bachelor's project that explored a similar setup involving an ESP32-based jammer and a Sodaq ExpLoRer device as the legitimate node. While we acknowledge and appreciate the foundational ideas from that work, the codebase used here has been extensively reworked and significantly expanded, resulting in a solution that is substantially different in both structure and implementation.

Additionally, we make use of the Sodaq_RN2483 library to interface with the LoRa module on the Sodaq device. Minor modifications have been made to the library to better suit the needs of this project, while the core functionality remains largely unchanged. We extend our thanks to the original authors for their work.
