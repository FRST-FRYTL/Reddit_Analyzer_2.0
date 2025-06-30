"""ASCII-based visualization utilities for terminal output."""

from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO

console = Console()


class ASCIIVisualizer:
    """ASCII-based visualization for terminal output."""

    def __init__(self):
        self.console = Console()

    def sentiment_bar_chart(self, data: Dict[str, int], title: str = "Sentiment Distribution") -> Table:
        """Create ASCII bar chart for sentiment distribution."""
        table = Table(title=title)
        table.add_column("Sentiment", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Percentage", style="green")
        table.add_column("Bar", style="blue")

        total = sum(data.values())
        max_width = 40

        for sentiment, count in data.items():
            percentage = (count / total) * 100 if total > 0 else 0
            bar_length = int((count / max(data.values())) * max_width) if data.values() else 0
            bar = "█" * bar_length

            table.add_row(
                sentiment.title(),
                str(count),
                f"{percentage:.1f}%",
                bar
            )

        return table

    def horizontal_bar_chart(self, data: Dict[str, int], title: str = "Data Chart", max_width: int = 40) -> Table:
        """Create horizontal ASCII bar chart."""
        table = Table(title=title)
        table.add_column("Item", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_column("Bar", style="blue")

        max_value = max(data.values()) if data.values() else 1

        for item, value in data.items():
            bar_length = int((value / max_value) * max_width)
            bar = "█" * bar_length

            table.add_row(
                item,
                str(value),
                bar
            )

        return table

    def trend_line_chart(self, dates: List[str], values: List[float], title: str) -> Panel:
        """Create ASCII line chart for trends."""
        if not dates or not values or len(dates) != len(values):
            return Panel("No data available", title=title, border_style="red")

        # Normalize values for ASCII display
        min_val, max_val = min(values), max(values)
        if min_val == max_val:
            # Handle case where all values are the same
            normalized = [5] * len(values)
        else:
            height = 10
            normalized = [(v - min_val) / (max_val - min_val) * height for v in values]

        width = min(60, len(values) * 2)
        
        lines = []
        for i in range(10, -1, -1):
            line = ""
            for j, norm_val in enumerate(normalized):
                if abs(norm_val - i) < 0.5:
                    line += "●"
                elif norm_val > i:
                    line += "│"
                else:
                    line += " "
                
                # Add spacing for readability
                if j < len(normalized) - 1:
                    line += " "
            lines.append(line)

        # Add axis
        axis_line = "└" + "─" * (len(line) - 1)
        lines.append(axis_line)
        
        # Add value indicators
        info_line = f"Range: {min_val:.1f} - {max_val:.1f}"
        lines.append(info_line)

        chart_text = "\n".join(lines)
        return Panel(chart_text, title=title, border_style="blue")

    def activity_heatmap(self, data: Dict[str, Dict[str, int]], title: str = "Activity Heatmap") -> Panel:
        """Create ASCII heatmap for activity data."""
        if not data:
            return Panel("No data available", title=title, border_style="red")

        # Get all hours and days
        days = list(data.keys())
        hours = set()
        for day_data in data.values():
            hours.update(day_data.keys())
        hours = sorted(hours)

        # Find max value for normalization
        max_value = 0
        for day_data in data.values():
            max_value = max(max_value, max(day_data.values()) if day_data.values() else 0)

        if max_value == 0:
            return Panel("No activity data", title=title, border_style="yellow")

        # Create heatmap characters
        chars = [" ", "░", "▒", "▓", "█"]
        
        lines = []
        
        # Header with hours
        header = "    " + "".join(f"{h:>3}" for h in hours[:24])  # Limit to 24 hours
        lines.append(header)
        
        # Data rows
        for day in days[-7:]:  # Last 7 days
            day_data = data.get(day, {})
            line = f"{day[:3]} "
            
            for hour in hours[:24]:
                value = day_data.get(hour, 0)
                intensity = int((value / max_value) * (len(chars) - 1))
                line += f" {chars[intensity]} "
            
            lines.append(line)

        chart_text = "\n".join(lines)
        return Panel(chart_text, title=title, border_style="green")

    def export_chart(self, data: Dict[str, int], chart_type: str, filename: str, title: str = "Reddit Data"):
        """Export chart as PNG using matplotlib."""
        try:
            plt.figure(figsize=(10, 6))
            plt.style.use('default')

            if chart_type == "bar":
                plt.bar(data.keys(), data.values())
                plt.xticks(rotation=45)
            elif chart_type == "line":
                plt.plot(list(data.keys()), list(data.values()), marker='o')
                plt.xticks(rotation=45)
            elif chart_type == "pie":
                plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%')

            plt.title(title)
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

            console.print(f"📊 Chart exported to {filename}", style="green")
            
        except Exception as e:
            console.print(f"❌ Failed to export chart: {e}", style="red")

    def create_summary_table(self, data: Dict[str, any], title: str = "Summary") -> Table:
        """Create a summary table for various data."""
        table = Table(title=title)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for key, value in data.items():
            # Format value based on type
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            elif isinstance(value, int):
                formatted_value = f"{value:,}"
            else:
                formatted_value = str(value)
                
            table.add_row(key.replace('_', ' ').title(), formatted_value)

        return table

    def progress_bar_ascii(self, current: int, total: int, width: int = 40) -> str:
        """Create ASCII progress bar."""
        if total == 0:
            percentage = 0
        else:
            percentage = (current / total) * 100
        
        filled_width = int(width * current // total) if total > 0 else 0
        bar = "█" * filled_width + "░" * (width - filled_width)
        
        return f"[{bar}] {percentage:.1f}% ({current}/{total})"