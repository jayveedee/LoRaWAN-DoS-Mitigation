# Airtime energy consumption calculator for TTN EU868
# https://avbentem.github.io/airtime-calculator/ttn/eu868/5
# E = V * I * T
# V is in Voltage (can be seen in radio datasheets, SX1276 and SX1262 are 3.3V)
# I is in Amperes (can be seen in radio datasheets, Heltec and SODAQ are 45mA and 40mA respectively)
# T is in seconds (calculated from airtime, can be seen in the airtime calculator)
# E is in Joules (calculated from the formula above)
sf9_heltec_e_4byte = (3.3 * 0.045 * 0.1649)
sf9_sodaq_e_4byte = (3.3 * 0.04 * 0.1649)
sf10_sodaq_e_4byte = (3.3 * 0.04 * 0.3297)
sf11_sodaq_e_4byte = (3.3 * 0.04 * 0.6595)
sf12_sodaq_e_4byte = (3.3 * 0.04 * 1.3189)

sf9_heltec_e_5byte = (3.3 * 0.045 * 0.1853)
sf9_sodaq_e_5byte = (3.3 * 0.04 * 0.1853)
sf10_sodaq_e_5byte = (3.3 * 0.04 * 0.3297)
sf11_sodaq_e_5byte = (3.3 * 0.04 * 0.6595)
sf12_sodaq_e_5byte = (3.3 * 0.04 * 1.3189)

# SODAQ
# Some strategies change spreading factor, so sometimes different calculations are done per message
e_standard_retry_4byte = sf9_sodaq_e_4byte * 51
e_dynamic_4byte = sf9_sodaq_e_4byte * 48 + sf10_sodaq_e_4byte * 2 + sf11_sodaq_e_4byte * 1
e_dynamic_sj_4byte = sf9_sodaq_e_4byte * 29 + sf10_sodaq_e_4byte * 22 + sf11_sodaq_e_4byte * 3
e_dynamic_dj_4byte = sf9_sodaq_e_4byte * 40 + sf10_sodaq_e_4byte * 7 + sf11_sodaq_e_4byte * 2 + sf12_sodaq_e_4byte * 2

e_standard_retry_5byte = sf9_sodaq_e_5byte * 51
e_dynamic_5byte = sf9_sodaq_e_5byte * 48 + sf10_sodaq_e_5byte * 2 + sf11_sodaq_e_5byte * 1
e_dynamic_sj_5byte = sf9_sodaq_e_5byte * 29 + sf10_sodaq_e_5byte * 22 + sf11_sodaq_e_5byte * 3
e_dynamic_dj_5byte = sf9_sodaq_e_5byte * 40 + sf10_sodaq_e_5byte * 7 + sf11_sodaq_e_5byte * 2 + sf12_sodaq_e_5byte * 2

# HELTEC
# PALBT sends 1 probe per message, so essentially double energy consumption (naive approach)
e_lbt_4byte = sf9_heltec_e_4byte * 51
e_palbt_4byte = sf9_heltec_e_4byte * 51 * 2

# Not so naive approach, probes are 1 byte and message is 5byte, effectively causing there to be a difference in transmission times
e_lbt_5byte = sf9_heltec_e_5byte * 51
e_palbt_5byte = sf9_heltec_e_5byte * 51 + sf9_heltec_e_4byte * 51 #4byte has the same airtime as 1byte

print(f"Energy consumption for 4Byte standard and retry: {e_standard_retry_4byte:.2f} J")
print(f"Energy consumption for 4Byte dynamic: {e_dynamic_4byte:.2f} J")
print(f"Energy consumption for 4Byte dynamic with SJ: {e_dynamic_sj_4byte:.2f} J")
print(f"Energy consumption for 4Byte dynamic with DJ: {e_dynamic_dj_4byte:.2f} J")
print(f"Energy consumption for 4Byte LBT: {e_lbt_4byte:.2f} J")
print(f"Energy consumption for 4Byte PALBT: {e_palbt_4byte:.2f} J")

print(f"Energy consumption for 5Byte standard and retry: {e_standard_retry_5byte:.2f} J")
print(f"Energy consumption for 5Byte dynamic: {e_dynamic_5byte:.2f} J")
print(f"Energy consumption for 5Byte dynamic with SJ: {e_dynamic_sj_5byte:.2f} J")
print(f"Energy consumption for 5Byte dynamic with DJ: {e_dynamic_dj_5byte:.2f} J")
print(f"Energy consumption for 5Byte LBT: {e_lbt_5byte:.2f} J")
print(f"Energy consumption for 5Byte PALBT: {e_palbt_5byte:.2f} J")