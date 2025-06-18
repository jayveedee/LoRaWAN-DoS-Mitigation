sf9_heltec_e = (3.3 * 0.045 * 0.1649)
sf9_sodaq_e = (3.3 * 0.04 * 0.1649)
sf10_sodaq_e = (3.3 * 0.04 * 0.3297)
sf11_sodaq_e = (3.3 * 0.04 * 0.6595)
sf12_sodaq_e = (3.3 * 0.04 * 1.3189)


e_standard_retry = sf9_sodaq_e * 51
e_dynamic = sf9_sodaq_e * 48 + sf10_sodaq_e * 2 + sf11_sodaq_e * 1
e_dynamic_sj = sf9_sodaq_e * 29 + sf10_sodaq_e * 22 + sf11_sodaq_e * 3
e_dynamic_dj = sf9_sodaq_e * 40 + sf10_sodaq_e * 7 + sf11_sodaq_e * 2 + sf12_sodaq_e * 2

e_lbt_palbt = sf9_heltec_e * 51

print(f"Energy consumption for standard and retry: {e_standard_retry:.2f} J")
print(f"Energy consumption for dynamic: {e_dynamic:.2f} J")
print(f"Energy consumption for dynamic with SJ: {e_dynamic_sj:.2f} J")
print(f"Energy consumption for dynamic with DJ: {e_dynamic_dj:.2f} J")
print(f"Energy consumption for LBT and PALBT: {e_lbt_palbt:.2f} J")