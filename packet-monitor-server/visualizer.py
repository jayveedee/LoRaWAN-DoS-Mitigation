import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
from datetime import datetime, timedelta
import glob
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class LoRaStatisticsVisualizer:
    """Visualize and analyze LoRa device statistics from CSV files"""
    
    def __init__(self, statistics_dir="statistics"):
        self.statistics_dir = statistics_dir
        self.output_dir = os.path.join(statistics_dir, "reports")
        self.ensure_output_directory()
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def ensure_output_directory(self):
        """Create output directory for reports and graphs"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def load_latest_statistics(self):
        """Load the most recent statistics file"""
        latest_file = os.path.join(self.statistics_dir, "latest_statistics.csv")
        
        if not os.path.exists(latest_file):
            # Try to find the most recent timestamped file
            pattern = os.path.join(self.statistics_dir, "device_statistics_*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError("No statistics files found")
            latest_file = max(files, key=os.path.getctime)
        
        try:
            df = pd.read_csv(latest_file)
            print(f"Loaded statistics from: {latest_file}")
            print(f"Data shape: {df.shape}")
            return df
        except Exception as e:
            print(f"Error loading statistics: {e}")
            return None
    
    def load_historical_statistics(self, days_back=7):
        """Load historical statistics for trend analysis"""
        pattern = os.path.join(self.statistics_dir, "device_statistics_*.csv")
        files = glob.glob(pattern)
        
        if not files:
            return None
            
        # Filter files from the last N days
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_files = []
        
        for file in files:
            try:
                # Extract timestamp from filename
                filename = os.path.basename(file)
                timestamp_str = filename.replace("device_statistics_", "").replace(".csv", "")
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                if file_date >= cutoff_date:
                    recent_files.append((file, file_date))
            except:
                continue
        
        if not recent_files:
            return None
        
        # Load and combine all recent files
        dfs = []
        for file, file_date in sorted(recent_files, key=lambda x: x[1]):
            try:
                df = pd.read_csv(file)
                df['snapshot_time'] = file_date
                dfs.append(df)
            except:
                continue
        
        if dfs:
            return pd.concat(dfs, ignore_index=True)
        return None
    
    def generate_device_overview(self, df):
        """Generate overview statistics for all devices"""
        if df is None or df.empty:
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('LoRa Device Network Overview', fontsize=16, fontweight='bold')
        
        # 1. Total Messages per Device
        ax1 = axes[0, 0]
        device_messages = df.nlargest(10, 'total_messages')
        bars1 = ax1.bar(range(len(device_messages)), device_messages['total_messages'])
        ax1.set_title('Top 10 Devices by Message Count')
        ax1.set_xlabel('Device Rank')
        ax1.set_ylabel('Total Messages')
        ax1.set_xticks(range(len(device_messages)))
        ax1.set_xticklabels([f"Dev {i+1}" for i in range(len(device_messages))], rotation=45)
        
        # Add value labels on bars
        for i, bar in enumerate(bars1):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{int(height)}', ha='center', va='bottom')
        
        # 2. RF Quality Distribution
        ax2 = axes[0, 1]
        quality_data = [
            df['rf_quality_good'].sum(),
            df['rf_quality_poor'].sum(),
            df['rf_quality_bad'].sum()
        ]
        labels = ['Good', 'Poor', 'Bad']
        colors = ['green', 'orange', 'red']
        wedges, texts, autotexts = ax2.pie(quality_data, labels=labels, colors=colors, autopct='%1.1f%%')
        ax2.set_title('RF Quality Distribution')
        
        # 3. RSSI Distribution
        ax3 = axes[0, 2]
        rssi_data = df['avg_rssi'][df['avg_rssi'] != 0]
        if not rssi_data.empty:
            ax3.hist(rssi_data, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax3.axvline(rssi_data.mean(), color='red', linestyle='--', 
                       label=f'Mean: {rssi_data.mean():.1f} dBm')
            ax3.set_title('RSSI Distribution')
            ax3.set_xlabel('RSSI (dBm)')
            ax3.set_ylabel('Number of Devices')
            ax3.legend()
        
        # 4. Frame Count Gaps
        ax4 = axes[1, 0]
        gap_devices = df[df['fcnt_gaps_count'] > 0].nlargest(10, 'fcnt_gaps_count')
        if not gap_devices.empty:
            bars4 = ax4.bar(range(len(gap_devices)), gap_devices['fcnt_gaps_count'])
            ax4.set_title('Devices with Most FCnt Gaps')
            ax4.set_xlabel('Device Rank')
            ax4.set_ylabel('Gap Count')
            ax4.set_xticks(range(len(gap_devices)))
            ax4.set_xticklabels([f"Dev {i+1}" for i in range(len(gap_devices))], rotation=45)
            
            # Add value labels
            for i, bar in enumerate(bars4):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{int(height)}', ha='center', va='bottom')
        
        # 5. Duplicate Messages
        ax5 = axes[1, 1]
        dup_devices = df[df['duplicate_count'] > 0].nlargest(10, 'duplicate_count')
        if not dup_devices.empty:
            bars5 = ax5.bar(range(len(dup_devices)), dup_devices['duplicate_count'])
            ax5.set_title('Devices with Most Duplicates')
            ax5.set_xlabel('Device Rank')
            ax5.set_ylabel('Duplicate Count')
            ax5.set_xticks(range(len(dup_devices)))
            ax5.set_xticklabels([f"Dev {i+1}" for i in range(len(dup_devices))], rotation=45)
            
            # Add value labels
            for i, bar in enumerate(bars5):
                height = bar.get_height()
                ax5.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{int(height)}', ha='center', va='bottom')
        
        # 6. SNR vs RSSI Scatter Plot
        ax6 = axes[1, 2]
        valid_data = df[(df['avg_rssi'] != 0) & (df['avg_snr'] != 0)]
        if not valid_data.empty:
            scatter = ax6.scatter(valid_data['avg_rssi'], valid_data['avg_snr'], 
                                alpha=0.6, c=valid_data['total_messages'], 
                                cmap='viridis', s=60)
            ax6.set_xlabel('Average RSSI (dBm)')
            ax6.set_ylabel('Average SNR (dB)')
            ax6.set_title('RSSI vs SNR (colored by message count)')
            plt.colorbar(scatter, ax=ax6, label='Message Count')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'device_overview.png'), dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_reliability_report(self, df):
        """Generate detailed reliability analysis"""
        if df is None or df.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Device Reliability Analysis', fontsize=16, fontweight='bold')
        
        # 1. Packet Loss Analysis
        ax1 = axes[0, 0]
        df['packet_loss_rate'] = (df['fcnt_gaps_total'] / df['total_messages'].replace(0, 1)) * 100
        loss_data = df[df['packet_loss_rate'] > 0].nlargest(10, 'packet_loss_rate')
        
        if not loss_data.empty:
            bars = ax1.barh(range(len(loss_data)), loss_data['packet_loss_rate'])
            ax1.set_title('Packet Loss Rate by Device')
            ax1.set_xlabel('Packet Loss Rate (%)')
            ax1.set_ylabel('Devices (ranked)')
            ax1.set_yticks(range(len(loss_data)))
            ax1.set_yticklabels([f"Device {i+1}" for i in range(len(loss_data))])
            
            # Color bars by severity
            for i, bar in enumerate(bars):
                rate = loss_data.iloc[i]['packet_loss_rate']
                if rate > 10:
                    bar.set_color('red')
                elif rate > 5:
                    bar.set_color('orange')
                else:
                    bar.set_color('yellow')
        
        # 2. Message Frequency Analysis
        ax2 = axes[0, 1]
        freq_data = df[['messages_last_hour', 'messages_last_day']].mean()
        ax2.bar(['Last Hour', 'Last Day'], freq_data.values, color=['lightblue', 'lightgreen'])
        ax2.set_title('Average Message Frequency')
        ax2.set_ylabel('Messages')
        
        # Add value labels
        for i, v in enumerate(freq_data.values):
            ax2.text(i, v + v*0.01, f'{v:.1f}', ha='center', va='bottom')
        
        # 3. Error Distribution
        ax3 = axes[1, 0]
        error_types = ['Payload Empty', 'Payload Repeated', 'Payload Corruption', 
                      'Timing Anomalies', 'Timestamp Errors']
        error_counts = [
            df['payload_empty'].sum(),
            df['payload_repeated'].sum(), 
            df['payload_corruption'].sum(),
            df['timing_anomalies'].sum(),
            df['timestamp_errors'].sum()
        ]
        
        bars = ax3.bar(error_types, error_counts, color=['red', 'orange', 'yellow', 'purple', 'brown'])
        ax3.set_title('Error Type Distribution')
        ax3.set_ylabel('Total Count')
        ax3.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar, count in zip(bars, error_counts):
            if count > 0:
                ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + bar.get_height()*0.01,
                        f'{int(count)}', ha='center', va='bottom')
        
        # 4. Device Health Score
        ax4 = axes[1, 1]
        # Calculate a simple health score (0-100)
        df['health_score'] = 100 - (
            (df['packet_loss_rate'] * 2) +
            (df['duplicate_count'] / df['total_messages'].replace(0, 1) * 100) +
            (df['timing_anomalies'] / df['total_messages'].replace(0, 1) * 100) +
            ((df['rf_quality_poor'] + df['rf_quality_bad'] * 2) / 
             (df['rf_quality_good'] + df['rf_quality_poor'] + df['rf_quality_bad']).replace(0, 1) * 50)
        ).clip(0, 100)
        
        health_bins = [0, 50, 70, 85, 100]
        health_labels = ['Critical', 'Poor', 'Fair', 'Good']
        health_counts = pd.cut(df['health_score'], bins=health_bins, labels=health_labels).value_counts()
        
        colors = ['red', 'orange', 'yellow', 'green']
        wedges, texts, autotexts = ax4.pie(health_counts.values, labels=health_counts.index, 
                                          colors=colors, autopct='%1.1f%%')
        ax4.set_title('Device Health Distribution')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'reliability_analysis.png'), dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_rf_analysis(self, df):
        """Generate RF performance analysis"""
        if df is None or df.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('RF Performance Analysis', fontsize=16, fontweight='bold')
        
        # Filter out invalid data
        valid_rf = df[(df['avg_rssi'] != 0) & (df['avg_snr'] != 0)]
        
        if valid_rf.empty:
            print("No valid RF data found")
            return
        
        # 1. RSSI Range Analysis
        ax1 = axes[0, 0]
        rssi_ranges = pd.cut(valid_rf['avg_rssi'], 
                           bins=[-200, -120, -110, -100, -90, -80, 0],
                           labels=['< -120', '-120 to -110', '-110 to -100', 
                                  '-100 to -90', '-90 to -80', '> -80'])
        rssi_counts = rssi_ranges.value_counts().sort_index()
        
        bars = ax1.bar(range(len(rssi_counts)), rssi_counts.values)
        ax1.set_title('RSSI Range Distribution')
        ax1.set_xlabel('RSSI Range (dBm)')
        ax1.set_ylabel('Number of Devices')
        ax1.set_xticks(range(len(rssi_counts)))
        ax1.set_xticklabels(rssi_counts.index, rotation=45)
        
        # Color bars by signal quality
        colors = ['red', 'orange', 'yellow', 'lightgreen', 'green', 'blue']
        for bar, color in zip(bars, colors[:len(bars)]):
            bar.set_color(color)
        
        # 2. SNR Distribution
        ax2 = axes[0, 1]
        ax2.hist(valid_rf['avg_snr'], bins=20, alpha=0.7, color='lightblue', edgecolor='black')
        ax2.axvline(valid_rf['avg_snr'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {valid_rf["avg_snr"].mean():.1f} dB')
        ax2.axvline(-10, color='orange', linestyle='--', label='Poor Threshold (-10 dB)')
        ax2.set_title('SNR Distribution')
        ax2.set_xlabel('SNR (dB)')
        ax2.set_ylabel('Number of Devices')
        ax2.legend()
        
        # 3. RSSI vs Message Count
        ax3 = axes[1, 0]
        ax3.scatter(valid_rf['avg_rssi'], valid_rf['total_messages'], alpha=0.6)
        ax3.set_xlabel('Average RSSI (dBm)')
        ax3.set_ylabel('Total Messages')
        ax3.set_title('Signal Strength vs Activity')
        
        # Add trend line
        if len(valid_rf) > 1:
            z = np.polyfit(valid_rf['avg_rssi'], valid_rf['total_messages'], 1)
            p = np.poly1d(z)
            ax3.plot(valid_rf['avg_rssi'], p(valid_rf['avg_rssi']), "r--", alpha=0.8)
        
        # 4. Gateway Coverage
        ax4 = axes[1, 1]
        df['avg_gateways'] = df['gateway_count_total'] / df['total_messages'].replace(0, 1)
        gateway_data = df[df['avg_gateways'] > 0]['avg_gateways']
        
        if not gateway_data.empty:
            ax4.hist(gateway_data, bins=10, alpha=0.7, color='lightgreen', edgecolor='black')
            ax4.axvline(gateway_data.mean(), color='red', linestyle='--', 
                       label=f'Mean: {gateway_data.mean():.1f}')
            ax4.set_title('Average Gateways per Message')
            ax4.set_xlabel('Average Gateway Count')
            ax4.set_ylabel('Number of Devices')
            ax4.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'rf_analysis.png'), dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_trend_analysis(self, historical_df):
        """Generate trend analysis from historical data"""
        if historical_df is None or historical_df.empty:
            print("No historical data available for trend analysis")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Trend Analysis', fontsize=16, fontweight='bold')
        
        # Group by snapshot time for trend analysis
        trends = historical_df.groupby('snapshot_time').agg({
            'total_messages': 'sum',
            'duplicate_count': 'sum',
            'fcnt_gaps_count': 'sum',
            'rf_quality_good': 'sum',
            'rf_quality_poor': 'sum',
            'rf_quality_bad': 'sum',
            'avg_rssi': 'mean',
            'avg_snr': 'mean'
        }).reset_index()
        
        # 1. Message Volume Trend
        ax1 = axes[0, 0]
        ax1.plot(trends['snapshot_time'], trends['total_messages'], marker='o', linewidth=2)
        ax1.set_title('Total Messages Over Time')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Total Messages')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # 2. Error Rate Trend
        ax2 = axes[0, 1]
        trends['error_rate'] = (trends['duplicate_count'] + trends['fcnt_gaps_count']) / trends['total_messages'] * 100
        ax2.plot(trends['snapshot_time'], trends['error_rate'], marker='o', color='red', linewidth=2)
        ax2.set_title('Error Rate Over Time')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Error Rate (%)')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # 3. RF Quality Trend
        ax3 = axes[1, 0]
        total_rf = trends['rf_quality_good'] + trends['rf_quality_poor'] + trends['rf_quality_bad']
        good_pct = trends['rf_quality_good'] / total_rf * 100
        poor_pct = trends['rf_quality_poor'] / total_rf * 100
        bad_pct = trends['rf_quality_bad'] / total_rf * 100
        
        ax3.plot(trends['snapshot_time'], good_pct, marker='o', color='green', label='Good', linewidth=2)
        ax3.plot(trends['snapshot_time'], poor_pct, marker='s', color='orange', label='Poor', linewidth=2)
        ax3.plot(trends['snapshot_time'], bad_pct, marker='^', color='red', label='Bad', linewidth=2)
        ax3.set_title('RF Quality Trend')
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Percentage')
        ax3.legend()
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)
        
        # 4. Average Signal Strength Trend
        ax4 = axes[1, 1]
        valid_rssi = trends[trends['avg_rssi'] != 0]
        if not valid_rssi.empty:
            ax4.plot(valid_rssi['snapshot_time'], valid_rssi['avg_rssi'], marker='o', color='blue', linewidth=2)
            ax4.set_title('Average RSSI Trend')
            ax4.set_xlabel('Time')
            ax4.set_ylabel('RSSI (dBm)')
            ax4.tick_params(axis='x', rotation=45)
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'trend_analysis.png'), dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_detailed_report(self, df):
        """Generate a comprehensive text report"""
        if df is None or df.empty:
            return
        
        report = []
        report.append("=" * 60)
        report.append("LORA NETWORK STATISTICS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Devices: {len(df)}")
        report.append("")
        
        # Network Overview
        report.append("NETWORK OVERVIEW")
        report.append("-" * 20)
        total_messages = df['total_messages'].sum()
        total_duplicates = df['duplicate_count'].sum()
        total_gaps = df['fcnt_gaps_count'].sum()
        
        report.append(f"Total Messages Received: {total_messages:,}")
        report.append(f"Total Duplicate Messages: {total_duplicates:,}")
        report.append(f"Total Frame Count Gaps: {total_gaps:,}")
        report.append(f"Overall Duplicate Rate: {(total_duplicates/total_messages*100):.2f}%")
        report.append("")
        
        # RF Quality Summary
        report.append("RF QUALITY SUMMARY")
        report.append("-" * 20)
        total_good = df['rf_quality_good'].sum()
        total_poor = df['rf_quality_poor'].sum()
        total_bad = df['rf_quality_bad'].sum()
        total_rf = total_good + total_poor + total_bad
        
        if total_rf > 0:
            report.append(f"Good Quality Messages: {total_good:,} ({total_good/total_rf*100:.1f}%)")
            report.append(f"Poor Quality Messages: {total_poor:,} ({total_poor/total_rf*100:.1f}%)")
            report.append(f"Bad Quality Messages: {total_bad:,} ({total_bad/total_rf*100:.1f}%)")
        
        valid_rssi = df[df['avg_rssi'] != 0]['avg_rssi']
        valid_snr = df[df['avg_snr'] != 0]['avg_snr']
        
        if not valid_rssi.empty:
            report.append(f"Average RSSI: {valid_rssi.mean():.1f} dBm")
            report.append(f"RSSI Range: {valid_rssi.min():.1f} to {valid_rssi.max():.1f} dBm")
        
        if not valid_snr.empty:
            report.append(f"Average SNR: {valid_snr.mean():.1f} dB")
            report.append(f"SNR Range: {valid_snr.min():.1f} to {valid_snr.max():.1f} dB")
        report.append("")
        
        # Top Problematic Devices
        report.append("TOP PROBLEMATIC DEVICES")
        report.append("-" * 25)
        
        # Devices with most gaps
        gap_devices = df[df['fcnt_gaps_count'] > 0].nlargest(5, 'fcnt_gaps_count')
        if not gap_devices.empty:
            report.append("Most Frame Count Gaps:")
            for i, (_, device) in enumerate(gap_devices.iterrows(), 1):
                report.append(f"  {i}. {device['dev_eui'][:16]}... - {device['fcnt_gaps_count']} gaps")
        
        # Devices with most duplicates
        dup_devices = df[df['duplicate_count'] > 0].nlargest(5, 'duplicate_count')
        if not dup_devices.empty:
            report.append("\nMost Duplicate Messages:")
            for i, (_, device) in enumerate(dup_devices.iterrows(), 1):
                report.append(f"  {i}. {device['dev_eui'][:16]}... - {device['duplicate_count']} duplicates")
        
        # Devices with worst RF quality
        df['rf_bad_ratio'] = df['rf_quality_bad'] / (df['rf_quality_good'] + df['rf_quality_poor'] + df['rf_quality_bad']).replace(0, 1)
        bad_rf_devices = df[df['rf_bad_ratio'] > 0].nlargest(5, 'rf_bad_ratio')
        if not bad_rf_devices.empty:
            report.append("\nWorst RF Quality:")
            for i, (_, device) in enumerate(bad_rf_devices.iterrows(), 1):
                report.append(f"  {i}. {device['dev_eui'][:16]}... - {device['rf_bad_ratio']*100:.1f}% bad quality")
        
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 15)
        
        if total_duplicates / total_messages > 0.05:
            report.append("• High duplicate rate detected - check for network congestion")
        
        if total_gaps / len(df) > 10:
            report.append("• High frame count gaps - investigate packet loss causes")
        
        if total_bad / total_rf > 0.1:
            report.append("• Many devices have poor RF quality - consider gateway placement")
        
        if len(df[df['avg_rssi'] < -115]) / len(df) > 0.2:
            report.append("• Many devices have weak signal strength - add more gateways")
        
        # Save report
        report_text = "\n".join(report)
        report_file = os.path.join(self.output_dir, f"network_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        print(report_text)
        print(f"\nDetailed report saved to: {report_file}")
    
    def run_full_analysis(self):
        """Run complete analysis and generate all reports"""
        print("Loading latest statistics...")
        df = self.load_latest_statistics()
        
        if df is None:
            print("No statistics data found!")
            return
        
        print(f"Analyzing {len(df)} devices...")
        
        # Generate all visualizations
        print("Generating device overview...")
        self.generate_device_overview(df)
        
        print("Generating reliability analysis...")
        self.generate_reliability_report(df)
        
        print("Generating RF analysis...")
        self.generate_rf_analysis(df)
        
        # Try to load historical data for trend analysis
        print("Loading historical data for trend analysis...")
        historical_df = self.load_historical_statistics(days_back=7)
        if historical_df is not None:
            print("Generating trend analysis...")
            self.generate_trend_analysis(historical_df)
        else:
            print("No historical data available for trend analysis")
        
        print("Generating detailed report...")
        self.generate_detailed_report(df)
        
        print(f"\nAll reports saved to: {self.output_dir}")

if __name__ == "__main__":
    # Create visualizer and run analysis
    visualizer = LoRaStatisticsVisualizer()
    visualizer.run_full_analysis()