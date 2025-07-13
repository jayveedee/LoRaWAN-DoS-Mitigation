import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Read the CSV data
# csv_data = "device-ttn-combined/4byte_stats_cleaned.csv"
csv_data = "device-ttn-combined/article/5byte_stats_cleaned.csv"

# Load data
df = pd.read_csv(csv_data)

# Clean and parse the data
df['MDR_numeric'] = df['MDR'].str.rstrip('%').astype(float)

# Extract strategy and jamming condition
df['Strategy'] = df['S'].str.extract(r'(.*?) \(')[0]
df['Jamming_Condition'] = df['S'].str.extract(r'\((.*?)\)')[0]

# Prepare plotting style
plt.style.use('default')
sns.set_palette("husl")

# Common variables
strategies = df['Strategy'].unique()
jamming_conditions = df['Jamming_Condition'].unique()
num_conditions = len(jamming_conditions)
x = np.arange(len(strategies)) * 1.5
width = 0.25
total_group_width = width * num_conditions
colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown']

# Create a comprehensive figure
fig = plt.figure(figsize=(20, 16))

# 1. Message Delivery Rate
ax1 = plt.subplot(3, 3, 1)
pivot_mdr = df.pivot(index='Strategy', columns='Jamming_Condition', values='MDR_numeric')
pivot_mdr.plot(kind='bar', ax=ax1, width=0.8)
ax1.set_title('Message Delivery Rate by Strategy\nunder Different Jamming Conditions', fontsize=12, fontweight='bold')
ax1.set_ylabel('Message Delivery Rate (%)')
ax1.set_xlabel('Strategy')
ax1.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
ax1.grid(True, alpha=0.3)
plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

# Save individual plot
fig_temp = plt.figure(figsize=(10, 6))
ax_temp = fig_temp.add_subplot(111)
pivot_mdr.plot(kind='bar', ax=ax_temp, width=0.8)
ax_temp.set_title('Message Delivery Rate by Strategy under Different Jamming Conditions', fontsize=14, fontweight='bold')
ax_temp.set_ylabel('Message Delivery Rate (%)')
ax_temp.set_xlabel('Strategy')
ax_temp.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
ax_temp.grid(True, alpha=0.3)
plt.setp(ax_temp.get_xticklabels(), rotation=45, ha='right')
plt.tight_layout()
plt.savefig('01_message_delivery_rate.eps', format='eps', bbox_inches='tight')
plt.close(fig_temp)

# 2. Energy Consumption
ax2 = plt.subplot(3, 3, 2)
pivot_ec = df.pivot(index='Strategy', columns='Jamming_Condition', values='EC')
pivot_ec.plot(kind='bar', ax=ax2, width=0.8)
ax2.set_title('Energy Consumption by Strategy\nunder Different Jamming Conditions', fontsize=12, fontweight='bold')
ax2.set_ylabel('Energy Consumption')
ax2.set_xlabel('Strategy')
ax2.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
ax2.grid(True, alpha=0.3)
plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')

fig_temp = plt.figure(figsize=(10, 6))
ax_temp = fig_temp.add_subplot(111)
pivot_ec.plot(kind='bar', ax=ax_temp, width=0.8)
ax_temp.set_title('Energy Consumption by Strategy under Different Jamming Conditions', fontsize=14, fontweight='bold')
ax_temp.set_ylabel('Energy Consumption')
ax_temp.set_xlabel('Strategy')
ax_temp.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
ax_temp.grid(True, alpha=0.3)
plt.setp(ax_temp.get_xticklabels(), rotation=45, ha='right')
plt.tight_layout()
plt.savefig('02_energy_consumption.eps', format='eps', bbox_inches='tight')
plt.close(fig_temp)

# 3. True Positives
ax3 = plt.subplot(3, 3, 3)
tp_table = df.pivot_table(index='Strategy', columns='Jamming_Condition', values='TP')
for i, condition in enumerate(jamming_conditions):
    bar_positions = x - total_group_width / 2 + i * width
    ax3.bar(bar_positions, tp_table[condition].reindex(strategies).values, width, label=f'{condition} - TP', alpha=1.0, color=colors[i])
ax3.set_title('True Positives by Strategy and Jamming Condition', fontsize=12, fontweight='bold')
ax3.set_ylabel('True Positives')
ax3.set_xlabel('Strategy')
ax3.set_xticks(x)
ax3.set_xticklabels(strategies, rotation=45, ha='right')
ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax3.grid(True, alpha=0.3)

# Save standalone figure
fig_temp = plt.figure(figsize=(10, 6))
ax_temp = fig_temp.add_subplot(111)
for i, condition in enumerate(jamming_conditions):
    bar_positions = x - total_group_width / 2 + i * width
    ax_temp.bar(bar_positions, tp_table[condition].reindex(strategies).values, width, label=f'{condition} - TP', alpha=0.8, color=colors[i])
ax_temp.set_title('True Positives by Strategy and Jamming Condition', fontsize=14, fontweight='bold')
ax_temp.set_ylabel('True Positives')
ax_temp.set_xlabel('Strategy')
ax_temp.set_xticks(x)
ax_temp.set_xticklabels(strategies, rotation=45, ha='right')
ax_temp.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax_temp.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('03_true_positives.eps', format='eps', bbox_inches='tight')
plt.close(fig_temp)

# 4. False Positives
ax4 = plt.subplot(3, 3, 4)
fp_table = df.pivot_table(index='Strategy', columns='Jamming_Condition', values='FP')
for i, condition in enumerate(jamming_conditions):
    ax4.bar(x + i*width, fp_table[condition].reindex(strategies).values, width, label=f'{condition} - FP', alpha=0.8, color=colors[i])
ax4.set_title('False Positives by Strategy and Jamming Condition', fontsize=12, fontweight='bold')
ax4.set_ylabel('False Positives')
ax4.set_xlabel('Strategy')
ax4.set_xticks(x + width)
ax4.set_xticklabels(strategies, rotation=45, ha='right')
ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax4.grid(True, alpha=0.3)

fig_temp = plt.figure(figsize=(10, 6))
ax_temp = fig_temp.add_subplot(111)
for i, condition in enumerate(jamming_conditions):
    ax_temp.bar(x + i*width, fp_table[condition].reindex(strategies).values, width, label=f'{condition} - FP', alpha=0.8, color=colors[i])
ax_temp.set_title('False Positives by Strategy and Jamming Condition', fontsize=14, fontweight='bold')
ax_temp.set_ylabel('False Positives')
ax_temp.set_xlabel('Strategy')
ax_temp.set_xticks(x + width)
ax_temp.set_xticklabels(strategies, rotation=45, ha='right')
ax_temp.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax_temp.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('04_false_positives.eps', format='eps', bbox_inches='tight')
plt.close(fig_temp)

# 5. Performance Efficiency (Scatter Plot)
ax5 = plt.subplot(3, 3, 5)
for condition in jamming_conditions:
    condition_data = df[df['Jamming_Condition'] == condition]
    ax5.scatter(condition_data['EC'], condition_data['MDR_numeric'], 
                label=condition, s=100, alpha=0.7)
    for idx, row in condition_data.iterrows():
        ax5.annotate(row['Strategy'][:10], (row['EC'], row['MDR_numeric']),
                     xytext=(5, 5), textcoords='offset points', fontsize=8, alpha=0.7)
ax5.set_title('Performance Efficiency:\nMessage Delivery Rate vs Energy Consumption', fontsize=12, fontweight='bold')
ax5.set_xlabel('Energy Consumption')
ax5.set_ylabel('Message Delivery Rate (%)')
ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax5.grid(True, alpha=0.3)

fig_temp = plt.figure(figsize=(10, 6))
ax_temp = fig_temp.add_subplot(111)
for condition in jamming_conditions:
    condition_data = df[df['Jamming_Condition'] == condition]
    ax_temp.scatter(condition_data['EC'], condition_data['MDR_numeric'], 
                    label=condition, s=100, alpha=0.7)
    for idx, row in condition_data.iterrows():
        ax_temp.annotate(row['Strategy'][:10], (row['EC'], row['MDR_numeric']),
                         xytext=(5, 5), textcoords='offset points', fontsize=8, alpha=0.7)
ax_temp.set_title('Performance Efficiency: Message Delivery Rate vs Energy Consumption', fontsize=14, fontweight='bold')
ax_temp.set_xlabel('Energy Consumption')
ax_temp.set_ylabel('Message Delivery Rate (%)')
ax_temp.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax_temp.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('05_performance_efficiency.eps', format='eps', bbox_inches='tight')
plt.close(fig_temp)

# 6. Heatmap of MDR
ax6 = plt.subplot(3, 3, 6)
heatmap_data = pivot_mdr.T
sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='RdYlGn', ax=ax6, cbar_kws={'label': 'MDR (%)'})
ax6.set_title('Message Delivery Rate Heatmap', fontsize=12, fontweight='bold')
ax6.set_xlabel('Strategy')
ax6.set_ylabel('Jamming Condition')

fig_temp = plt.figure(figsize=(10, 6))
ax_temp = fig_temp.add_subplot(111)
sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='RdYlGn', ax=ax_temp, cbar_kws={'label': 'MDR (%)'})
ax_temp.set_title('Message Delivery Rate Heatmap', fontsize=14, fontweight='bold')
ax_temp.set_xlabel('Strategy')
ax_temp.set_ylabel('Jamming Condition')
plt.tight_layout()
plt.savefig('06_mdr_heatmap.eps', format='eps', bbox_inches='tight')
plt.close(fig_temp)

# 7. Precision
df['Precision'] = df['TP'] / (df['TP'] + df['FP'])
df['Recall'] = df['TP'] / (df['TP'] + df['FN'])
df['F1_Score'] = 2 * (df['Precision'] * df['Recall']) / (df['Precision'] + df['Recall'])

# Handle divide-by-zero
df['Precision'] = df['Precision'].fillna(0)
df['Recall'] = df['Recall'].fillna(0)
df['F1_Score'] = df['F1_Score'].fillna(0)

ax7 = plt.subplot(3, 3, 7)
pivot_precision = df.pivot(index='Strategy', columns='Jamming_Condition', values='Precision')
pivot_precision.plot(kind='bar', ax=ax7, width=0.8)
ax7.set_title('Precision by Strategy under Different Jamming Conditions', fontsize=12, fontweight='bold')
ax7.set_ylabel('Precision')
ax7.set_xlabel('Strategy')
ax7.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
ax7.grid(True, alpha=0.3)
plt.setp(ax7.get_xticklabels(), rotation=45, ha='right')

# Save individual plot
fig_temp = plt.figure(figsize=(10, 6))
ax_temp = fig_temp.add_subplot(111)
pivot_precision.plot(kind='bar', ax=ax_temp, width=0.8)
ax_temp.set_title('Precision by Strategy under Different Jamming Conditions', fontsize=14, fontweight='bold')
ax_temp.set_ylabel('Precision')
ax_temp.set_xlabel('Strategy')
ax_temp.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
ax_temp.grid(True, alpha=0.3)
plt.setp(ax_temp.get_xticklabels(), rotation=45, ha='right')
plt.tight_layout()
plt.savefig('07_precision_analysis.eps', format='eps', bbox_inches='tight')
plt.close(fig_temp)

# 8. Robustness Analysis (Performance drop under jamming)
ax8 = plt.subplot(3, 3, 8)
no_jamming_mdr = df[df['Jamming_Condition'] == 'No Jamming']['MDR_numeric'].values
static_jamming_device_mdr = df[df['Jamming_Condition'] == 'Static Jamming Device']['MDR_numeric'].values
static_jamming_gateway_mdr = df[df['Jamming_Condition'] == 'Static Jamming Gateway']['MDR_numeric'].values
dynamic_jamming_device_mdr = df[df['Jamming_Condition'] == 'Dynamic Jamming Device']['MDR_numeric'].values
dynamic_jamming_gateway_mdr = df[df['Jamming_Condition'] == 'Dynamic Jamming Gateway']['MDR_numeric'].values

static_device_drop = no_jamming_mdr - static_jamming_device_mdr # type: ignore
static_gateway_drop = no_jamming_mdr - static_jamming_gateway_mdr # type: ignore
dynamic_device_drop = no_jamming_mdr - dynamic_jamming_device_mdr # type: ignore
dynamic_gateway_drop = no_jamming_mdr - dynamic_jamming_gateway_mdr # type: ignore

ax8.bar(x - 0.2, static_device_drop, 0.4, label='Static Jamming Device Impact', alpha=0.8)
ax8.bar(x - 0.2, static_gateway_drop, 0.4, label='Static Jamming Gateway Impact', alpha=0.8)
ax8.bar(x + 0.2, dynamic_device_drop, 0.4, label='Dynamic Jamming Device Impact', alpha=0.8)
ax8.bar(x + 0.2, dynamic_gateway_drop, 0.4, label='Dynamic Jamming Device Impact', alpha=0.8)

ax8.set_title('Robustness Analysis:\nPerformance Drop under Jamming', fontsize=12, fontweight='bold')
ax8.set_ylabel('MDR Drop (%)')
ax8.set_xlabel('Strategy')
ax8.set_xticks(x)
ax8.set_xticklabels(strategies, rotation=45, ha='right')
ax8.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax8.grid(True, alpha=0.3)

# Save individual plot
fig_temp = plt.figure(figsize=(10, 6))
ax_temp = fig_temp.add_subplot(111)
ax_temp.bar(x - 0.2, static_device_drop, 0.4, label='Static Jamming Device Impact', alpha=0.8)
ax_temp.bar(x - 0.2, static_gateway_drop, 0.4, label='Static Jamming Gateway Impact', alpha=0.8)
ax_temp.bar(x + 0.2, dynamic_device_drop, 0.4, label='Dynamic Jamming Device Impact', alpha=0.8)
ax_temp.bar(x + 0.2, dynamic_gateway_drop, 0.4, label='Dynamic Jamming Gateway Impact', alpha=0.8)
ax_temp.set_title('Robustness Analysis: Performance Drop under Jamming', fontsize=14, fontweight='bold')
ax_temp.set_ylabel('MDR Drop (%)')
ax_temp.set_xlabel('Strategy')
ax_temp.set_xticks(x)
ax_temp.set_xticklabels(strategies, rotation=45, ha='right')
ax_temp.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax_temp.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('08_robustness_analysis.eps', format='eps', bbox_inches='tight')
plt.close(fig_temp)

# 9. Overall Performance Score
ax9 = plt.subplot(3, 3, 9)
# Calculate normalized performance score (MDR weight: 0.6, Energy efficiency weight: 0.4)
df['Energy_Efficiency'] = 1 / df['EC']  # Inverse of energy consumption
df['Performance_Score'] = (df['MDR_numeric'] * 0.6) + (df['Energy_Efficiency'] * 40 * 0.4)

pivot_score = df.pivot(index='Strategy', columns='Jamming_Condition', values='Performance_Score')
pivot_score.plot(kind='bar', ax=ax9, width=0.8)
ax9.set_title('Overall Performance Score\n(60% MDR + 40% Energy Efficiency)', fontsize=12, fontweight='bold')
ax9.set_ylabel('Performance Score')
ax9.set_xlabel('Strategy')
ax9.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
ax9.grid(True, alpha=0.3)
plt.setp(ax9.get_xticklabels(), rotation=45, ha='right')

# Save individual plot
fig_temp = plt.figure(figsize=(10, 6))
ax_temp = fig_temp.add_subplot(111)
pivot_score.plot(kind='bar', ax=ax_temp, width=0.8)
ax_temp.set_title('Overall Performance Score (60% MDR + 40% Energy Efficiency)', fontsize=14, fontweight='bold')
ax_temp.set_ylabel('Performance Score')
ax_temp.set_xlabel('Strategy')
ax_temp.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
ax_temp.grid(True, alpha=0.3)
plt.setp(ax_temp.get_xticklabels(), rotation=45, ha='right')
plt.tight_layout()
plt.savefig('09_overall_performance_score.eps', format='eps', bbox_inches='tight')
plt.close(fig_temp)

plt.tight_layout()
plt.savefig('lorawan_performance_analysis.eps', format='eps', bbox_inches='tight')
plt.show()

# Print summary statistics
print("=== PERFORMANCE ANALYSIS SUMMARY ===\n")

print("1. MESSAGE DELIVERY RATE STATISTICS:")
print(df.groupby('Jamming_Condition')['MDR_numeric'].agg(['mean', 'std', 'min', 'max']).round(2))

print("\n2. ENERGY CONSUMPTION STATISTICS:")
print(df.groupby('Jamming_Condition')['EC'].agg(['mean', 'std', 'min', 'max']).round(2))

print("\n3. BEST PERFORMING STRATEGIES BY CONDITION:")
for condition in jamming_conditions:
    best_strategy = df[df['Jamming_Condition'] == condition].nlargest(1, 'MDR_numeric')
    print(f"{condition}: {best_strategy['Strategy'].iloc[0]} (MDR: {best_strategy['MDR_numeric'].iloc[0]}%)")

print("\n4. MOST ROBUST STRATEGIES (smallest performance drop):")
robustness_data = []
for strategy in strategies:
    strategy_data = df[df['Strategy'] == strategy]
    no_jam = strategy_data[strategy_data['Jamming_Condition'] == 'No Jamming']['MDR_numeric'].iloc[0]
    static_device_jam = strategy_data[strategy_data['Jamming_Condition'] == 'Static Jamming Device']['MDR_numeric'].iloc[0]
    static_gateway_jam = strategy_data[strategy_data['Jamming_Condition'] == 'Static Jamming Gateway']['MDR_numeric'].iloc[0]
    dynamic_device_jam = strategy_data[strategy_data['Jamming_Condition'] == 'Dynamic Jamming Device']['MDR_numeric'].iloc[0]
    dynamic_gateway_jam = strategy_data[strategy_data['Jamming_Condition'] == 'Dynamic Jamming Gateway']['MDR_numeric'].iloc[0]
    
    avg_drop = ((no_jam - static_device_jam) + (no_jam - static_gateway_jam) + (no_jam - dynamic_device_jam) + (no_jam - dynamic_gateway_jam)) / 4
    robustness_data.append((strategy, avg_drop))

robustness_data.sort(key=lambda x: x[1])
for strategy, drop in robustness_data:
    print(f"{strategy}: Average drop of {drop:.1f}%")

print("\n5. ENERGY EFFICIENCY RANKINGS:")
efficiency_data = []
for strategy in strategies:
    strategy_data = df[df['Strategy'] == strategy]
    avg_mdr = strategy_data['MDR_numeric'].mean()
    avg_ec = strategy_data['EC'].mean()
    efficiency = avg_mdr / avg_ec
    efficiency_data.append((strategy, efficiency))

efficiency_data.sort(key=lambda x: x[1], reverse=True)
for strategy, eff in efficiency_data:
    print(f"{strategy}: {eff:.1f} (MDR/Energy ratio)")