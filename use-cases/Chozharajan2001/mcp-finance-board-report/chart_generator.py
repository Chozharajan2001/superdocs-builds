"""
Visual Financial Chart Rendering Engine.
Generates publication-quality charts from data warehouse metrics for embedding in board packets.
"""
from pathlib import Path
from typing import Optional
import os


class FinancialChartGenerator:
    """Renders charts as PNG or SVG images for document embedding."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (Path(__file__).parent / "generated_charts")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_arr_growth_chart(self, filename: str = "arr_growth_bridge.png") -> Path:
        """Renders ARR bridge and quarterly growth chart."""
        chart_path = self.output_dir / filename
        
        # Check if matplotlib is available
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8, 4.5), dpi=200)
            fig.patch.set_facecolor('#0f172a')
            ax.set_facecolor('#1e293b')

            quarters = ['Q3 2025', 'Q4 2025', 'Q1 2026', 'Q2 2026']
            arr_values = [13.3, 15.8, 18.45, 22.40]

            bars = ax.bar(quarters, arr_values, color=['#6366f1', '#818cf8', '#38bdf8', '#10b981'], width=0.55, edgecolor='#334155')
            ax.plot(quarters, arr_values, color='#34d399', marker='o', linewidth=2.5, markersize=8)

            ax.set_title('Quarterly ARR Growth ($M) • +68.5% YoY', color='#f8fafc', fontsize=14, fontweight='bold', pad=15)
            ax.set_ylabel('Annual Recurring Revenue ($M)', color='#94a3b8', fontsize=11)
            ax.tick_params(colors='#94a3b8')
            ax.grid(axis='y', color='#334155', linestyle='--', alpha=0.7)

            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'${height:.2f}M',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 5),
                            textcoords="offset points",
                            ha='center', va='bottom', color='#f8fafc', fontweight='bold')

            plt.tight_layout()
            plt.savefig(chart_path, facecolor=fig.get_facecolor(), edgecolor='none')
            plt.close()
        except ImportError:
            # Standalone fallback image generator using basic binary canvas
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 450), color='#0f172a')
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 750, 400], fill='#1e293b', outline='#334155')
            draw.text((70, 70), "Quarterly ARR Growth: $13.3M -> $22.4M (+68.5% YoY)", fill='#10b981')
            draw.rectangle([100, 250, 180, 360], fill='#6366f1')
            draw.rectangle([250, 210, 330, 360], fill='#818cf8')
            draw.rectangle([400, 170, 480, 360], fill='#38bdf8')
            draw.rectangle([550, 110, 630, 360], fill='#10b981')
            img.save(chart_path)

        return chart_path

    def render_unit_economics_chart(self, filename: str = "unit_economics.png") -> Path:
        """Renders CAC Payback, NDR, and Gross Margin KPI chart."""
        chart_path = self.output_dir / filename
        
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
            fig.patch.set_facecolor('#0f172a')
            ax.set_facecolor('#1e293b')

            metrics = ['Net Dollar Retention', 'Gross Margin', 'LTV : CAC (x10)', 'CAC Payback (Mo)']
            values = [124.2, 81.4, 46.0, 10.8]
            colors = ['#10b981', '#38bdf8', '#a855f7', '#f59e0b']

            bars = ax.barh(metrics, values, color=colors, height=0.5, edgecolor='#334155')
            ax.set_title('SaaS Unit Economics & Efficiency Benchmarks (Q2 2026)', color='#f8fafc', fontsize=13, fontweight='bold', pad=12)
            ax.tick_params(colors='#94a3b8')
            ax.grid(axis='x', color='#334155', linestyle='--', alpha=0.7)

            for bar in bars:
                width = bar.get_width()
                label = f"{width:.1f}%" if width > 50 else f"{width:.1f}"
                ax.annotate(f' {label}',
                            xy=(width, bar.get_y() + bar.get_height() / 2),
                            xytext=(3, 0),
                            textcoords="offset points",
                            ha='left', va='center', color='#f8fafc', fontweight='bold')

            plt.tight_layout()
            plt.savefig(chart_path, facecolor=fig.get_facecolor(), edgecolor='none')
            plt.close()
        except ImportError:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 400), color='#0f172a')
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), "Unit Economics: NDR 124.2% | Gross Margin 81.4% | CAC Payback 10.8mo", fill='#38bdf8')
            img.save(chart_path)

        return chart_path
