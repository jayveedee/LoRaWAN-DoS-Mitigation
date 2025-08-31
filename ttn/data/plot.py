import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class PlotConfig:
    """Configuration for plot styling and layout"""
    figsize: Tuple[int, int] = (10, 6)
    title_fontsize: int = 14
    title_fontweight: str = 'bold'
    rotation: int = 45
    ha: str = 'right'
    alpha: float = 0.3
    width: float = 0.8
    colors: Optional[Dict[str, str]] = None
    condition_abbreviations: Optional[Dict[str, str]] = None
    output_format: str = 'eps'  
    dpi: int = 300 
    
    def __post_init__(self):
        if self.colors is None:
            self.colors = {
                'Dynamic Jamming Device': 'tab:cyan',
                'Dynamic Jamming Gateway': 'tab:purple',
                'No Jamming': 'tab:blue',
                'Static Jamming Device': 'tab:orange',
                'Static Jamming Gateway': 'tab:green'
            }
        if self.condition_abbreviations is None:
            self.condition_abbreviations = {
                'Dynamic Jamming Device': 'DynDev',
                'Dynamic Jamming Gateway': 'DynGW',
                'No Jamming': 'NoJam',
                'Static Jamming Device': 'StatDev',
                'Static Jamming Gateway': 'StatGW'
            }


class LoRaWANAnalyzer:
    """Main analyzer class for LoRaWAN performance data"""
    
    def __init__(self, csv_path: str, config: PlotConfig = None):
        self.csv_path: str = csv_path
        self.config: PlotConfig = config or PlotConfig()
        self.df: Optional[pd.DataFrame] = None
        self.strategies: Optional[np.ndarray] = None
        self.jamming_conditions: Optional[List[str]] = None
        self.x_positions: Optional[np.ndarray] = None
        
    def load_and_preprocess_data(self) -> pd.DataFrame:
        """Load CSV data and perform preprocessing"""
        self.df = pd.read_csv(self.csv_path)
        
        # Clean and parse the data
        self.df['MDR_numeric'] = self.df['MDR'].str.rstrip('%').astype(float)
        self.df['Strategy'] = self.df['S'].str.extract(r'(.*?) \(')[0]
        self.df['Jamming_Condition'] = self.df['S'].str.extract(r'\((.*?)\)')[0]
        
        # Calculate derived metrics
        self.df['Precision'] = self.df['TP'] / (self.df['TP'] + self.df['FP'])
        self.df['Recall'] = self.df['TP'] / (self.df['TP'] + self.df['FN'])
        self.df['F1_Score'] = 2 * (self.df['Precision'] * self.df['Recall']) / (self.df['Precision'] + self.df['Recall'])
        self.df['Energy_Efficiency'] = 1 / self.df['EC']
        self.df['Performance_Score'] = (self.df['MDR_numeric'] * 0.6) + (self.df['Energy_Efficiency'] * 40 * 0.4)
        
        # Handle divide-by-zero
        for col in ['Precision', 'Recall', 'F1_Score']:
            self.df[col] = self.df[col].fillna(0)
        
        # Set up common variables with consistent order
        self.strategies = self.df['Strategy'].unique()
        # Define the consistent order for jamming conditions
        self.jamming_conditions = [
            'Dynamic Jamming Device',
            'Dynamic Jamming Gateway', 
            'No Jamming',
            'Static Jamming Device',
            'Static Jamming Gateway'
        ]
        # Filter to only include conditions that actually exist in the data
        self.jamming_conditions = [cond for cond in self.jamming_conditions 
                                 if cond in self.df['Jamming_Condition'].unique()]
        
        self.x_positions = np.arange(len(self.strategies)) * 1.5
        
        return self.df
    
    def setup_plot_style(self):
        """Configure matplotlib and seaborn styling"""
        plt.style.use('default')
        sns.set_palette("husl")


class PlotGenerator:
    """Handles plot generation and saving"""
    
    def __init__(self, analyzer: LoRaWANAnalyzer):
        self.analyzer = analyzer
        self.config = analyzer.config
        
    def _get_filename_with_extension(self, base_filename: str) -> str:
        """Convert base filename to include proper extension"""
        # Remove existing extension if present
        base_name = os.path.splitext(base_filename)[0]
        return f"{base_name}.{self.config.output_format}"
    
    def _save_figure(self, fig, filename: str):
        """Save figure with appropriate format and settings"""
        actual_filename = self._get_filename_with_extension(filename)
        
        if self.config.output_format.lower() == 'png':
            fig.savefig(actual_filename, format='png', dpi=self.config.dpi, bbox_inches='tight')
        elif self.config.output_format.lower() == 'eps':
            fig.savefig(actual_filename, format='eps', bbox_inches='tight')
        else:
            raise ValueError(f"Unsupported output format: {self.config.output_format}")
        
        print(f"Saved plot: {actual_filename}")
        
    def create_and_save_plot(self, plot_func, filename: str, title: str, **kwargs):
        """Generic method to create, display, and save plots"""
        # Create individual plot
        fig, ax = plt.subplots(figsize=self.config.figsize)
        plot_func(ax, title, **kwargs)
        self._finalize_plot(ax, title)
        plt.tight_layout()
        self._save_figure(fig, filename)
        plt.close(fig)
        
        # Return axis for subplot usage
        return lambda ax_sub: plot_func(ax_sub, title, **kwargs)
    
    def _finalize_plot(self, ax, title: str):
        """Apply common plot finalization"""
        ax.set_title(title, fontsize=self.config.title_fontsize, 
                    fontweight=self.config.title_fontweight)
        handles, _ = ax.get_legend_handles_labels()
        if handles:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=self.config.alpha)
        
    def _setup_bar_plot(self, ax, title: str, xlabel: str, ylabel: str, rotation: bool = True):
        """Common setup for bar plots"""
        ax.set_title(title, fontsize=self.config.title_fontsize, 
                    fontweight=self.config.title_fontweight)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=self.config.alpha)
        if rotation:
            plt.setp(ax.get_xticklabels(), rotation=self.config.rotation, ha=self.config.ha)
    
    def plot_pivot_bar(self, ax, title: str, data_column: str, xlabel: str, ylabel: str):
        """Create pivot bar plot"""
        # Assertions
        assert self.config.colors is not None, "PlotConfig.colors must not be None"
        assert self.analyzer.df is not None, "LoRaWANAnalyzer.df must not be None"

        pivot_data = self.analyzer.df.pivot(index='Strategy', columns='Jamming_Condition', values=data_column)
        
        # Reorder columns to match desired legend order
        pivot_data = pivot_data.reindex(columns=self.analyzer.jamming_conditions)
        
        # Create bars with consistent colors
        colors = [self.config.colors[col] for col in pivot_data.columns]
        pivot_data.plot(kind='bar', ax=ax, width=self.config.width, color=colors)
        
        self._setup_bar_plot(ax, title, xlabel, ylabel)
        ax.legend(title='Jamming Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    def plot_grouped_bar(self, ax, title: str, data_column: str, xlabel: str, ylabel: str, label_suffix: str = ''):
        """Create grouped bar plot"""
        # Assertions
        assert self.config.colors is not None, "PlotConfig.colors must not be None"
        assert self.analyzer.df is not None, "LoRaWANAnalyzer.df must not be None"
        assert self.analyzer.x_positions is not None, "LoRaWANAnalyzer.x_positions must not be None"
        assert self.analyzer.jamming_conditions is not None, "LoRaWANAnalyzer.jamming_conditions must not be None"
        
        pivot_data = self.analyzer.df.pivot_table(index='Strategy', columns='Jamming_Condition', values=data_column)
        width = 0.25
        total_width = width * len(self.analyzer.jamming_conditions)
        
        # Use the ordered jamming conditions
        for i, condition in enumerate(self.analyzer.jamming_conditions):
            positions = self.analyzer.x_positions - total_width / 2 + i * width
            values = pivot_data[condition].reindex(self.analyzer.strategies).values
            color = self.config.colors[condition]
            ax.bar(positions, values, width, label=f'{condition}{label_suffix}', 
                  alpha=0.8, color=color)
        
        self._setup_bar_plot(ax, title, xlabel, ylabel)
        ax.set_xticks(self.analyzer.x_positions)
        ax.set_xticklabels(self.analyzer.strategies, rotation=self.config.rotation, ha=self.config.ha)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    def plot_scatter(self, ax, title: str, x_column: str, y_column: str, xlabel: str, ylabel: str):
        """Create scatter plot"""
        # Assertions
        assert self.config.colors is not None, "PlotConfig.colors must not be None"
        assert self.config.condition_abbreviations is not None, "PlotConfig.condition_abbreviations must not be None"
        assert self.analyzer.df is not None, "LoRaWANAnalyzer.df must not be None"
        assert self.analyzer.jamming_conditions is not None, "LoRaWANAnalyzer.jamming_conditions must not be None"

        offsets = [
            (10, 0), (15, 5), (15, -5), (20, 0),
            (10, 10), (10, -10), (25, 5), (25, -5),
            (15, 15), (15, -15), (30, 0), (20, 10)
        ]
    
        offset_index = 0
        
        # Use the ordered jamming conditions
        for condition in self.analyzer.jamming_conditions:
            condition_data = self.analyzer.df[self.analyzer.df['Jamming_Condition'] == condition]
            color = self.config.colors[condition]
            ax.scatter(condition_data[x_column], condition_data[y_column],
                    label=condition, s=100, alpha=0.7, color=color)
            
            # Add annotations with cycling offsets and styling
            for _, row in condition_data.iterrows():
                abbrev = self.config.condition_abbreviations[row['Jamming_Condition']]
                scatter_title = f"{row['Strategy'].replace('Sodaq', '')} ({abbrev})"
                
                # Use cycling offsets to reduce overlaps
                current_offset = offsets[offset_index % len(offsets)]
                
                ax.annotate(scatter_title, (row[x_column], row[y_column]),
                        xytext=current_offset, textcoords='offset points', 
                        fontsize=8, alpha=0.8,
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                                alpha=0.8, edgecolor='gray', linewidth=0.5),
                        arrowprops=dict(arrowstyle='->', alpha=0.6, color='gray'))
                
                offset_index += 1
        
        self._setup_bar_plot(ax, title, xlabel, ylabel, rotation=False)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    def plot_heatmap(self, ax, title: str, data_column: str, xlabel: str, ylabel: str, cbar_label: str):
        """Create heatmap"""
        # Assertions
        assert self.analyzer.df is not None, "LoRaWANAnalyzer.df must not be None"

        pivot_data = self.analyzer.df.pivot(index='Strategy', columns='Jamming_Condition', values=data_column)
        
        # Reorder columns to match desired legend order
        pivot_data = pivot_data.reindex(columns=self.analyzer.jamming_conditions)
        
        heatmap_data = pivot_data.T
        sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='RdYlGn', ax=ax, 
                   cbar_kws={'label': cbar_label})
        ax.set_title(title, fontsize=self.config.title_fontsize, fontweight=self.config.title_fontweight)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
    
    def plot_robustness_analysis(self, ax, title: str):
        """Create robustness analysis plot"""
        # Assertions
        assert self.config.colors is not None, "PlotConfig.colors must not be None"
        assert self.analyzer.df is not None, "LoRaWANAnalyzer.df must not be None"
        assert self.analyzer.x_positions is not None, "LoRaWANAnalyzer.x_positions must not be None"
        assert self.analyzer.jamming_conditions is not None, "LoRaWANAnalyzer.jamming_conditions must not be None"

        # Calculate performance drops
        no_jamming_mdr = np.asarray(self.analyzer.df[self.analyzer.df['Jamming_Condition'] == 'No Jamming']['MDR_numeric'].values)
        
        drops = {}
        # Use only jamming conditions (exclude 'No Jamming')
        jamming_conditions = [cond for cond in self.analyzer.jamming_conditions if cond != 'No Jamming']
        
        for condition in jamming_conditions:
            condition_mdr = np.asarray(self.analyzer.df[self.analyzer.df['Jamming_Condition'] == condition]['MDR_numeric'].values)
            drops[condition] = no_jamming_mdr - condition_mdr
        
        # Plot bars in the consistent order
        x = self.analyzer.x_positions
        width = 0.2
        for i, condition in enumerate(jamming_conditions):
            drop_values = drops[condition]
            positions = x + (i - 1.5) * width
            color = self.config.colors[condition]
            ax.bar(positions, drop_values, width, label=f'{condition} Impact', 
                  alpha=0.8, color=color)
        
        self._setup_bar_plot(ax, title, 'Strategy', 'MDR Drop (%)')
        ax.set_xticks(x)
        ax.set_xticklabels(self.analyzer.strategies, rotation=self.config.rotation, ha=self.config.ha)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')


class ReportGenerator:
    """Generates summary statistics and reports"""
    
    def __init__(self, analyzer: LoRaWANAnalyzer):
        self.analyzer = analyzer
    
    def print_summary_statistics(self):
        """Print comprehensive summary statistics"""
        # Assertions
        assert self.analyzer.df is not None, "LoRaWANAnalyzer.df must not be None"
        assert self.analyzer.jamming_conditions is not None, "LoRaWANAnalyzer.jamming_conditions must not be None"
        assert self.analyzer.strategies is not None, "LoRaWANAnalyzer.strategies must not be None"

        print("=== PERFORMANCE ANALYSIS SUMMARY ===\n")
        
        print("1. MESSAGE DELIVERY RATE STATISTICS:")
        print(self.analyzer.df.groupby('Jamming_Condition')['MDR_numeric'].agg(['mean', 'std', 'min', 'max']).round(2))
        
        print("\n2. ENERGY CONSUMPTION STATISTICS:")
        print(self.analyzer.df.groupby('Jamming_Condition')['EC'].agg(['mean', 'std', 'min', 'max']).round(2))
        
        print("\n3. BEST PERFORMING STRATEGIES BY CONDITION:")
        for condition in self.analyzer.jamming_conditions:
            best_strategy = self.analyzer.df[self.analyzer.df['Jamming_Condition'] == condition].nlargest(1, 'MDR_numeric')
            print(f"{condition}: {best_strategy['Strategy'].iloc[0]} (MDR: {best_strategy['MDR_numeric'].iloc[0]}%)")
        
        print("\n4. MOST ROBUST STRATEGIES (smallest performance drop):")
        robustness_data = self._calculate_robustness()
        for strategy, drop in robustness_data:
            print(f"{strategy}: Average drop of {drop:.1f}%")
        
        print("\n5. ENERGY EFFICIENCY RANKINGS:")
        efficiency_data = self._calculate_efficiency_rankings()
        for strategy, eff in efficiency_data:
            print(f"{strategy}: {eff:.1f} (MDR/Energy ratio)")
    
    def _calculate_robustness(self) -> List[Tuple[str, float]]:
        """Calculate robustness metrics for each strategy"""
        # Assertions
        assert self.analyzer.df is not None, "LoRaWANAnalyzer.df must not be None"
        assert self.analyzer.strategies is not None, "LoRaWANAnalyzer.strategies must not be None"
        assert self.analyzer.jamming_conditions is not None, "LoRaWANAnalyzer.jamming_conditions must not be None"

        robustness_data = []
        for strategy in self.analyzer.strategies:
            strategy_data = self.analyzer.df[self.analyzer.df['Strategy'] == strategy]
            no_jam = strategy_data[strategy_data['Jamming_Condition'] == 'No Jamming']['MDR_numeric'].iloc[0]
            
            drops = []
            # Use only jamming conditions (exclude 'No Jamming')
            jamming_conditions = [cond for cond in self.analyzer.jamming_conditions if cond != 'No Jamming']
            for condition in jamming_conditions:
                jam_mdr = strategy_data[strategy_data['Jamming_Condition'] == condition]['MDR_numeric'].iloc[0]
                drops.append(no_jam - jam_mdr)
            
            avg_drop = np.mean(drops)
            robustness_data.append((strategy, avg_drop))
        
        return sorted(robustness_data, key=lambda x: x[1])
    
    def _calculate_efficiency_rankings(self) -> List[Tuple[str, float]]:
        """Calculate energy efficiency rankings"""
        # Assertions
        assert self.analyzer.df is not None, "LoRaWANAnalyzer.df must not be None"
        assert self.analyzer.strategies is not None, "LoRaWANAnalyzer.strategies must not be None"

        efficiency_data = []
        for strategy in self.analyzer.strategies:
            strategy_data = self.analyzer.df[self.analyzer.df['Strategy'] == strategy]
            avg_mdr = strategy_data['MDR_numeric'].mean()
            avg_ec = strategy_data['EC'].mean()
            efficiency = avg_mdr / avg_ec
            efficiency_data.append((strategy, efficiency))
        
        return sorted(efficiency_data, key=lambda x: x[1], reverse=True)


def main():
    """Main execution function"""
    # Configuration
    output_format = 'eps'  # Change to 'png' or 'eps'
    output_dir = 'plots/'
    csv_data = "device-ttn-combined/article/5byte_stats_cleaned.csv"
    
    config = PlotConfig(figsize=(10, 6), output_format=output_format, dpi=300)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Print current format being used
    print(f"Saving plots in {config.output_format.upper()} format")
    if config.output_format.lower() == 'png':
        print(f"PNG DPI: {config.dpi}")
    
    # Initialize analyzer
    analyzer = LoRaWANAnalyzer(csv_data, config)
    analyzer.load_and_preprocess_data()
    analyzer.setup_plot_style()
    
    # Initialize plot generator
    plot_gen = PlotGenerator(analyzer)
    
    # Define plots configuration (note: extensions will be automatically handled)
    plots_config = [
        {
            'func': plot_gen.plot_pivot_bar,
            'filename': output_dir + 'mdr-pivot-bar',
            'title': 'Message Delivery by Strategy Under Jamming',
            'data_column': 'MDR_numeric',
            'xlabel': 'Strategy',
            'ylabel': 'Message Delivery Rate (%)'
        },
        {
            'func': plot_gen.plot_pivot_bar,
            'filename': output_dir + 'ec-pivot-bar',
            'title': 'Energy Use by Strategy Under Jamming',
            'data_column': 'EC',
            'xlabel': 'Strategy',
            'ylabel': 'Energy Consumption'
        },
        {
            'func': plot_gen.plot_grouped_bar,
            'filename': output_dir + 'tp-grouped-bar',
            'title': 'True Positives by Strategy & Jamming',
            'data_column': 'TP',
            'xlabel': 'Strategy',
            'ylabel': 'True Positives',
            'label_suffix': ' - TP'
        },
        {
            'func': plot_gen.plot_grouped_bar,
            'filename': output_dir + 'fp-grouped-bar',
            'title': 'False Positives by Strategy & Jamming',
            'data_column': 'FP',
            'xlabel': 'Strategy',
            'ylabel': 'False Positives',
            'label_suffix': ' - FP'
        },
        {
            'func': plot_gen.plot_scatter,
            'filename': output_dir + 'ec-scatter',
            'title': 'Energy Consumption vs Message Delivery Rate',
            'x_column': 'EC',
            'y_column': 'MDR_numeric',
            'xlabel': 'Energy Consumption',
            'ylabel': 'Message Delivery Rate (%)'
        },
        {
            'func': plot_gen.plot_heatmap,
            'filename': output_dir + 'mdr-heatmap',
            'title': 'Message Delivery Rate Heatmap',
            'data_column': 'MDR_numeric',
            'xlabel': 'Strategy',
            'ylabel': 'Jamming Condition',
            'cbar_label': 'MDR (%)',
            'alpha': 0
        },
        {
            'func': plot_gen.plot_pivot_bar,
            'filename': output_dir + 'precision-pivot-bar',
            'title': 'Precision by Strategy Under Jamming',
            'data_column': 'Precision',
            'xlabel': 'Strategy',
            'ylabel': 'Precision'
        },
        {
            'func': plot_gen.plot_robustness_analysis,
            'filename': output_dir + 'robustness-pivot-bar',
            'title': 'Robustness: Performance Drop Under Jamming',
        },
        {
            'func': plot_gen.plot_pivot_bar,
            'filename': output_dir + 'overall-performance-pivot-bar',
            'title': 'Overall Performance (60% MDR, 40% EC)',
            'data_column': 'Performance_Score',
            'xlabel': 'Strategy',
            'ylabel': 'Performance Score'
        }
    ]
    
    # Create comprehensive figure - collect subplot functions
    subplot_funcs = []
    
    # Generate individual plots and collect subplot functions
    for i, plot_config in enumerate(plots_config, 1):
        func = plot_config.pop('func')
        filename = plot_config.pop('filename')
        title = plot_config.pop('title')
        config.alpha = plot_config.pop('alpha', config.alpha)
        
        subplot_func = plot_gen.create_and_save_plot(func, filename, title, **plot_config)
        subplot_funcs.append(subplot_func)
    
    # Create combined subplot figure
    combined_fig = plt.figure(figsize=(20, 16))
    for i, subplot_func in enumerate(subplot_funcs, 1):
        ax = plt.subplot(3, 3, i)
        subplot_func(ax)
    
    plt.tight_layout()
    
    # Save the combined figure with the appropriate extension
    combined_filename = output_dir + 'combined-plots'
    plot_gen._save_figure(combined_fig, combined_filename)
    #plt.show()
    
    # Generate report
    report_gen = ReportGenerator(analyzer)
    report_gen.print_summary_statistics()

if __name__ == "__main__":
    main()