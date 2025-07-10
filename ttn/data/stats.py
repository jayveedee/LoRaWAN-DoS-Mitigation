import os
import json
import pandas as pd

class LoRaWANAnalyzer:
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
        self.files_data = self._load_all_files()  # [(filename, [entries])]

    def _load_all_files(self):
        file_entries = []
        for filename in os.listdir(self.folder_path):
            if filename.lower().endswith(".json"):
                file_path = os.path.join(self.folder_path, filename)
                try:
                    with open(file_path, "r") as f:
                        content = json.load(f)
                        if isinstance(content, list):
                            entries = [entry for entry in content if isinstance(entry, dict)]
                        elif isinstance(content, dict):
                            entries = [content]
                        else:
                            entries = []
                        file_entries.append((filename, entries))
                except (json.JSONDecodeError, OSError) as e:
                    print(f"Skipping {filename} due to error: {e}")
        return file_entries

    def analyze_all(self, expected_count=50):
        for filename, entries in self.files_data:
            self._analyze_file(filename, entries, expected_count)

    def _analyze_file(self, filename, data, expected_count):
        dev_addr_counts = {}
        for entry in data:
            try:
                dev_addr = entry["data"]["message"]["payload"]["mac_payload"]["f_hdr"]["dev_addr"]
                dev_addr_counts[dev_addr] = dev_addr_counts.get(dev_addr, 0) + 1
            except KeyError:
                continue

        if not dev_addr_counts:
            print(f"\n{filename}: No dev_addr found.")
            return

        target_dev_addr = max(dev_addr_counts, key=dev_addr_counts.get)

        f_cnt_values = []
        missing_fcnt = []

        for entry in data:
            try:
                mac_payload = entry["data"]["message"]["payload"]["mac_payload"]
                dev_addr = mac_payload["f_hdr"].get("dev_addr")
                if dev_addr == target_dev_addr:
                    f_cnt = mac_payload["f_hdr"].get("f_cnt")
                    if f_cnt is not None and f_cnt <= expected_count:
                        f_cnt_values.append(f_cnt)
                    else:
                        missing_fcnt.append(entry)
            except KeyError:
                continue

        received_count = len(set(f_cnt_values)) + 1
        lost_count = expected_count - received_count
        success_rate = received_count / expected_count * 100
        loss_rate = lost_count / expected_count * 100

        df = pd.DataFrame({
            #"File": [filename],
            "Target Dev Addr": [target_dev_addr],
            "Total Sent": [expected_count],
            "Received": [received_count],
            "Lost": [lost_count],
            "Success Rate (%)": [round(success_rate, 2)],
            "Loss Rate (%)": [round(loss_rate, 2)]
        })

        print(f"Results for file: {filename}")
        print(df.to_string(index=False))
        print("\n")

# Example usage
if __name__ == "__main__":
    analyzer = LoRaWANAnalyzer("logs/article/")
    analyzer.analyze_all()
