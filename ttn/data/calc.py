# Airtime energy consumption calculator for TTN EU868
# https://avbentem.github.io/airtime-calculator/ttn/eu868/5
# E = V * I * T
# V is in Voltage (can be seen in radio datasheets, SX1276 and SX1262 are 3.3V)
# I is in Amperes (can be seen in radio datasheets, Heltec and SODAQ are 45mA and 40mA respectively)
# T is in seconds (calculated from airtime, can be seen in the airtime calculator)
# E is in Joules (calculated from the formula above)

class EnergyCalculator:
    def __init__(self, voltage: float, current: float, airtimes: dict):
        """
        :param voltage: Voltage in volts
        :param current: Current in amperes
        :param airtimes: Dictionary with spreading factors (e.g., "SF9_4B") as keys and airtime in seconds as values
        """
        self.voltage = voltage
        self.current = current
        self.airtimes = airtimes  # e.g., {"SF9_4B": 0.1649, "SF9_5B": 0.1853, ...}

    def energy(self, sf: str) -> float:
        return self.voltage * self.current * self.airtimes[sf]

    def total_energy(self, strategy: dict) -> float:
        return sum(self.energy(sf) * count for sf, count in strategy.items())

# Airtime values for SODAQ and HELTEC
sodaq_airtimes = {
    "SF9_4B": 0.1649,
    "SF10_4B": 0.3297,
    "SF11_4B": 0.6595,
    "SF12_4B": 1.3189,
    "SF9_5B": 0.1853,
    "SF10_5B": 0.3297,
    "SF11_5B": 0.6595,
    "SF12_5B": 1.3189,
}

heltec_airtimes = {
    "SF9_4B": 0.1649,
    "SF9_5B": 0.1853,
}

# Instantiate calculators
sodaq_calc = EnergyCalculator(voltage=3.3, current=0.04, airtimes=sodaq_airtimes)
heltec_calc = EnergyCalculator(voltage=3.3, current=0.045, airtimes=heltec_airtimes)

# Define strategies
# strategies = {
#     "e_standard_retry_4byte": {"SF9_4B": 51},
#     "e_dynamic_4byte": {"SF9_4B": 48, "SF10_4B": 2, "SF11_4B": 1},
#     "e_dynamic_sj_4byte": {"SF9_4B": 29, "SF10_4B": 22, "SF11_4B": 3},
#     "e_dynamic_dj_4byte": {"SF9_4B": 40, "SF10_4B": 7, "SF11_4B": 2, "SF12_4B": 2},
#     "e_standard_retry_5byte": {"SF9_5B": 51},
#     "e_dynamic_5byte": {"SF9_5B": 48, "SF10_5B": 2, "SF11_5B": 1},
#     "e_dynamic_sj_5byte": {"SF9_5B": 29, "SF10_5B": 22, "SF11_5B": 3},
#     "e_dynamic_dj_5byte": {"SF9_5B": 40, "SF10_5B": 7, "SF11_5B": 2, "SF12_5B": 2},
#     "e_lbt_4byte": {"SF9_4B": 51},
#     "e_palbt_4byte": {"SF9_4B": 51 * 2},
#     "e_lbt_5byte": {"SF9_5B": 51},
#     "e_palbt_5byte": {"SF9_5B": 51, "SF9_4B": 51},  # probe is 1B ~ 4B airtime
# }

strategies = {
    "e_standard_+_retry+dynamic_none": {"SF9_5B": 50},
    "e_dynamic_sj_device": {"SF9_5B": 27, "SF10_5B": 19, "SF11_5B": 4},
    "e_dynamic_sj_gateway": {"SF9_5B": 24, "SF10_5B": 16, "SF11_5B": 10},
    "e_dynamic_dj_device": {"SF9_5B": 39, "SF10_5B": 7, "SF11_5B": 3, "SF12_5B": 1},
    "e_dynamic_dj_gateway": {"SF9_5B": 45, "SF10_5B": 5},
}

# Print results
print("=== SODAQ ===")
for name, strat in strategies.items():
    if "palbt" in name or "lbt" in name:
        continue  # skip HELTEC-specific strategies
    energy = sodaq_calc.total_energy(strat)
    print(f"{name}: {energy:.2f} J")

print("\n=== HELTEC ===")
for name, strat in strategies.items():
    if not ("palbt" in name or "lbt" in name):
        continue
    energy = heltec_calc.total_energy(strat)
    print(f"{name}: {energy:.2f} J")
