import json
import pandas as pd

# Load the JSON data
with open("../samples/actual_data/sodaq_std_no_jamming.json", "r") as f:
    data = json.load(f)

# Automatically find all unique dev_addrs
dev_addr_counts = {}
for entry in data:
    try:
        dev_addr = entry["data"]["message"]["payload"]["mac_payload"]["f_hdr"]["dev_addr"]
        if dev_addr in dev_addr_counts:
            dev_addr_counts[dev_addr] += 1
        else:
            dev_addr_counts[dev_addr] = 1
    except KeyError:
        continue

# For simplicity, pick the most frequent dev_addr as the target
if dev_addr_counts:
    target_dev_addr = max(dev_addr_counts, key=dev_addr_counts.get)
else:
    target_dev_addr = None

# Collect f_cnt values for the target_dev_addr
f_cnt_values = []
missing_fcnt = []

for entry in data:
    try:
        mac_payload = entry["data"]["message"]["payload"]["mac_payload"]
        dev_addr = mac_payload["f_hdr"].get("dev_addr", None)

        if dev_addr == target_dev_addr:
            f_cnt = mac_payload["f_hdr"].get("f_cnt", None)
            if f_cnt is not None and f_cnt <= 50:
                f_cnt_values.append(f_cnt)
            else:
                missing_fcnt.append(entry)
    except KeyError:
        continue

# Analysis
expected_count = 50+1
received_count = len(set(f_cnt_values))+1
lost_count = expected_count - received_count
success_rate = received_count / expected_count * 100
loss_rate = lost_count / expected_count * 100

# Prepare the result DataFrame
df = pd.DataFrame({
    "Target Dev Addr": [target_dev_addr],
    "Total Sent": [expected_count],
    "Received": [received_count],
    "Lost": [lost_count],
    "Success Rate (%)": [round(success_rate, 2)],
    "Loss Rate (%)": [round(loss_rate, 2)]
})
print(f)
print(df)

# import json
# import pandas as pd

# # Use forward slashes or raw string for Windows path
# with open("data\\transmission_noAck_Jamming.json", "r") as f:
#     data = json.load(f)

# # Define your target device address
# target_dev_addr = "260B62F1"

# # Store found f_cnts and missing ones
# f_cnt_values = []
# missing_fcnt = []

# for entry in data:
#     try:
#         mac_payload = entry["data"]["message"]["payload"]["mac_payload"]
#         dev_addr = mac_payload["f_hdr"].get("dev_addr", None)

#         if dev_addr == target_dev_addr:
#             f_cnt = mac_payload["f_hdr"].get("f_cnt", None)
#             if f_cnt is not None:
#                 f_cnt_values.append(f_cnt)
#             else:
#                 missing_fcnt.append(entry)
#     except KeyError:
#         continue

# # Count packets
# received_count = len(set(f_cnt_values))
# expected_count = 20
# lost_count = expected_count - received_count
# success_rate = received_count / expected_count * 100
# loss_rate = lost_count / expected_count * 100

# # Print stats
# df = pd.DataFrame({
#     "Total Sent": [expected_count],
#     "Received": [received_count],
#     "Lost": [lost_count],
#     "Success Rate (%)": [round(success_rate, 2)],
#     "Loss Rate (%)": [round(loss_rate, 2)]
# })

# print(df)

# # Optional: show packets with missing f_cnt
# print(f"\nFound {len(missing_fcnt)} packet(s) with missing f_cnt.")
# for i, pkt in enumerate(missing_fcnt, 1):
#     print(f"\nPacket {i}:")
#     print(json.dumps(pkt, indent=2))
