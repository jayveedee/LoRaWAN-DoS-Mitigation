# LoRaWAN-DoS-Mitigation
Master thesis project about LoRaWAN DoS Mitigation.

## Authors of the repository

- `Jákup Viljam Dam` `s185095` `Computer Science and Engineering`
- `Mohammad Tawrat Nafiu Uddin` `s184174` `Computer Science and Engineering`

## How it works
We're simulating a situation where there is a jammer (ESP32) trying to disrupt a device (Sodaq ExpLoRer) using reactive jamming on the PHY layer.
The jammer listens for the preamble of the legitimate device on all channels and only starts transmitting if it detects some transmission. Doing so, will create a DoS attack on the legitimate device. However, the main focus on this project is to try to detect and mitigate the attack on the legitimate device, so that the device may be better prepared to handle such events. So when running the code, the final product will be a jammer trying to jam a device which in turn tries to decieve or handle the situation better.

## Installation
How to install and run the project

### Prerequisites
- You must have a TTN server set up which must also be configured for the devices for OTAA
- You must use the following devices
  1. ESP32 with the LoRa chip: `SX1276`
  2. Sodaq ExpLoRer with the LoRa chip: `RN2483` 
  3. Dragino_LPS8N set up to the TTN network via OTAA
- The following Arduino libraries
  1. RadioLib
  2. Sodaq_wdt
- The following Arduino board managers
  1. SODAQ SAMD Boards
  2. ESP32

### Usage
1. Clone the Repo:
2. Connect your devices to your PC via USB
3. Compile and flash the devices with the code provided
   - For the ESP32, use the `esp32.ino` code in the `esp32/` directory
   - For the Sodaq ExpLoRer, use the `sodaq.ino` code in the `sodaq/` directory 
     - Remember to modify the OTAA configuration in the code to join the TTN network
4. When the code has been flashed, the devices should be up and running

## Acknowledgements
- In this project we make use of the library: Sodaq_RN2483, which we've modified a bit to fit our purposes
- The Sodaq and ESP32 code initally was built upon from a previous bachelor's project, where the code was close-sourced, however much of the code has been changed since but inspiration was definitely taken from there