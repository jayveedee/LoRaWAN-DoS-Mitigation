import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Read the CSV data
csv_data = "device-ttn-combined/stats.csv"

# Load data
df = pd.read_csv(csv_data)

# Clean and parse the data
df['MDR_numeric'] = df['MDR'].str.rstrip('%').astype(float)

# Extract strategy and jamming condition
df['Strategy'] = df['S'].str.extract(r'(.*?) \(')[0]
df['Jamming_Condition'] = df['S'].str.extract(r'\((.*?);')[0]

# Set up the plotting style
plt.style.use('default')
sns.set_palette("husl")

# Create a comprehensive analysis with multiple subplots
fig = plt.figure(figsize=(20, 16))

# 1. Message Delivery Rate by Strategy and Jamming Condition
ax1 = plt.subplot(3, 3, 1)
pivot_mdr = df.pivot(index='Strategy', columns='Jamming_Condition', values='MDR_numeric')
pivot_mdr.plot(kind='bar', ax=ax1, width=0.8)
ax1.set_title('Message Delivery Rate by Strategy\nunder Different Jamming Conditions', fontsize=12, fontweight='bold')
ax1.set_ylabel('Message Delivery Rate (%)')
ax1.set_xlabel('Strategy')
ax1.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
ax1.grid(True, alpha=0.3)
plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

# 2. Energy Consumption Analysis
ax2 = plt.subplot(3, 3, 2)
pivot_ec = df.pivot(index='Strategy', columns='Jamming_Condition', values='EC')
pivot_ec.plot(kind='bar', ax=ax2, width=0.8)
ax2.set_title('Energy Consumption by Strategy\nunder Different Jamming Conditions', fontsize=12, fontweight='bold')
ax2.set_ylabel('Energy Consumption')
ax2.set_xlabel('Strategy')
ax2.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
ax2.grid(True, alpha=0.3)
plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')

# 3. True Positives vs False Positives
ax3 = plt.subplot(3, 3, 3)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
jamming_conditions = df['Jamming_Condition'].unique()
x = np.arange(len(df['Strategy'].unique()))
width = 0.25

for i, condition in enumerate(jamming_conditions):
    condition_data = df[df['Jamming_Condition'] == condition]
    tp_values = condition_data['TP'].values
    ax3.bar(x + i*width, tp_values, width, label=f'{condition} - TP', alpha=0.8, color=colors[i])

ax3.set_title('True Positives by Strategy and Jamming Condition', fontsize=12, fontweight='bold')
ax3.set_ylabel('True Positives')
ax3.set_xlabel('Strategy')
ax3.set_xticks(x + width)
ax3.set_xticklabels(df['Strategy'].unique(), rotation=45, ha='right')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. False Positives Analysis
ax4 = plt.subplot(3, 3, 4)
for i, condition in enumerate(jamming_conditions):
    condition_data = df[df['Jamming_Condition'] == condition]
    fp_values = condition_data['FP'].values
    ax4.bar(x + i*width, fp_values, width, label=f'{condition} - FP', alpha=0.8, color=colors[i])

ax4.set_title('False Positives by Strategy and Jamming Condition', fontsize=12, fontweight='bold')
ax4.set_ylabel('False Positives')
ax4.set_xlabel('Strategy')
ax4.set_xticks(x + width)
ax4.set_xticklabels(df['Strategy'].unique(), rotation=45, ha='right')
ax4.legend()
ax4.grid(True, alpha=0.3)

# 5. Performance Efficiency (MDR vs Energy Consumption)
ax5 = plt.subplot(3, 3, 5)
for condition in jamming_conditions:
    condition_data = df[df['Jamming_Condition'] == condition]
    ax5.scatter(condition_data['EC'], condition_data['MDR_numeric'], 
               label=condition, s=100, alpha=0.7)
    
    # Add strategy labels
    for idx, row in condition_data.iterrows():
        ax5.annotate(row['Strategy'][:10], 
                    (row['EC'], row['MDR_numeric']),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=8, alpha=0.7)

ax5.set_title('Performance Efficiency:\nMessage Delivery Rate vs Energy Consumption', fontsize=12, fontweight='bold')
ax5.set_xlabel('Energy Consumption')
ax5.set_ylabel('Message Delivery Rate (%)')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 6. Heatmap of Message Delivery Rates
ax6 = plt.subplot(3, 3, 6)
heatmap_data = pivot_mdr.T
sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='RdYlGn', 
            ax=ax6, cbar_kws={'label': 'MDR (%)'})
ax6.set_title('Message Delivery Rate Heatmap', fontsize=12, fontweight='bold')
ax6.set_xlabel('Strategy')
ax6.set_ylabel('Jamming Condition')

# 7. Precision and Recall Calculation
df['Precision'] = df['TP'] / (df['TP'] + df['FP'])
df['Recall'] = df['TP'] / (df['TP'] + df['FN'])
df['F1_Score'] = 2 * (df['Precision'] * df['Recall']) / (df['Precision'] + df['Recall'])

# Handle division by zero
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

# 8. Robustness Analysis (Performance drop under jamming)
ax8 = plt.subplot(3, 3, 8)
no_jamming_mdr = df[df['Jamming_Condition'] == 'No Jamming']['MDR_numeric'].values
static_jamming_mdr = df[df['Jamming_Condition'] == 'Static Jamming']['MDR_numeric'].values
dynamic_jamming_mdr = df[df['Jamming_Condition'] == 'Dynamic Jamming']['MDR_numeric'].values

static_drop = no_jamming_mdr - static_jamming_mdr
dynamic_drop = no_jamming_mdr - dynamic_jamming_mdr

strategies = df['Strategy'].unique()
x = np.arange(len(strategies))

ax8.bar(x - 0.2, static_drop, 0.4, label='Static Jamming Impact', alpha=0.8)
ax8.bar(x + 0.2, dynamic_drop, 0.4, label='Dynamic Jamming Impact', alpha=0.8)

ax8.set_title('Robustness Analysis:\nPerformance Drop under Jamming', fontsize=12, fontweight='bold')
ax8.set_ylabel('MDR Drop (%)')
ax8.set_xlabel('Strategy')
ax8.set_xticks(x)
ax8.set_xticklabels(strategies, rotation=45, ha='right')
ax8.legend()
ax8.grid(True, alpha=0.3)

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

plt.tight_layout()
plt.savefig('lorawan_performance_analysis.png', dpi=300, bbox_inches='tight')
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
    static_jam = strategy_data[strategy_data['Jamming_Condition'] == 'Static Jamming']['MDR_numeric'].iloc[0]
    dynamic_jam = strategy_data[strategy_data['Jamming_Condition'] == 'Dynamic Jamming']['MDR_numeric'].iloc[0]
    
    avg_drop = ((no_jam - static_jam) + (no_jam - dynamic_jam)) / 2
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