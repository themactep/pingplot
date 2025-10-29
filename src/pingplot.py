#!/usr/bin/env python3
"""
PingPlot - Visualize ping latency as a graph with CLI output support.
"""

import subprocess
import re
import sys
import json
from typing import List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PingResult:
    """Represents a single ping result."""
    sequence: int
    latency: float  # in milliseconds


class PingPlotter:
    """Handles ping execution and visualization."""

    def __init__(self, host: str, count: int = 100, interval: float = 0.1, packet_size: int = 1400):
        self.host = host
        self.count = count
        self.interval = interval
        self.packet_size = packet_size
        self.results: List[PingResult] = []

    def run_ping(self) -> bool:
        """Execute ping command and parse results."""
        cmd = [
            "ping",
            "-c", str(self.count),
            "-i", str(self.interval),
            "-s", str(self.packet_size),
            self.host
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            self._parse_ping_output(result.stdout)
            return True
        except subprocess.TimeoutExpired:
            print("Error: Ping command timed out", file=sys.stderr)
            return False
        except FileNotFoundError:
            print("Error: ping command not found", file=sys.stderr)
            return False

    def _parse_ping_output(self, output: str) -> None:
        """Parse ping output and extract latency values."""
        # Pattern: "bytes=1400 seq=0 ttl=64 time=1.234 ms"
        pattern = r"seq=(\d+).*time=([0-9.]+)\s*ms"
        
        for line in output.split('\n'):
            match = re.search(pattern, line)
            if match:
                seq = int(match.group(1))
                latency = float(match.group(2))
                self.results.append(PingResult(sequence=seq, latency=latency))

    def get_stats(self) -> dict:
        """Calculate statistics from ping results."""
        if not self.results:
            return {}

        latencies = [r.latency for r in self.results]
        return {
            "count": len(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "avg": sum(latencies) / len(latencies),
            "lost": self.count - len(latencies),
        }

    def plot_ascii(self, height: int = 20, width: int = 80) -> str:
        """Generate ASCII graph of latency over time."""
        if not self.results:
            return "No ping results to plot"

        latencies = [r.latency for r in self.results]
        min_lat = min(latencies)
        max_lat = max(latencies)
        range_lat = max_lat - min_lat if max_lat > min_lat else 1

        # Normalize latencies to height
        normalized = [
            int((lat - min_lat) / range_lat * (height - 1))
            for lat in latencies
        ]

        # Create graph
        graph = [[' ' for _ in range(width)] for _ in range(height)]

        # Plot points (sample if too many results)
        step = max(1, len(normalized) // width)
        for i, norm_lat in enumerate(normalized[::step]):
            x = min(i, width - 1)
            y = height - 1 - norm_lat
            graph[y][x] = '█'

        # Convert to string
        lines = [''.join(row) for row in graph]
        
        # Add axis labels
        stats = self.get_stats()
        header = f"Latency Graph (min: {stats['min']:.2f}ms, max: {stats['max']:.2f}ms, avg: {stats['avg']:.2f}ms)"
        footer = f"Time →"
        
        return header + '\n' + '\n'.join(lines) + '\n' + footer

    def to_json(self) -> str:
        """Export results as JSON."""
        stats = self.get_stats()
        data = {
            "host": self.host,
            "stats": stats,
            "results": [
                {"sequence": r.sequence, "latency": r.latency}
                for r in self.results
            ]
        }
        return json.dumps(data, indent=2)

    def to_csv(self) -> str:
        """Export results as CSV."""
        lines = ["sequence,latency_ms"]
        for r in self.results:
            lines.append(f"{r.sequence},{r.latency}")
        return '\n'.join(lines)

    def plot_matplotlib(self, output_file: str = "pingplot.png", figsize: Tuple[int, int] = (12, 6)) -> str:
        """Generate a matplotlib graph and save as image."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib is required for image output. Install with: pip install matplotlib")

        if not self.results:
            raise ValueError("No ping results to plot")

        sequences = [r.sequence for r in self.results]
        latencies = [r.latency for r in self.results]
        stats = self.get_stats()

        fig, ax = plt.subplots(figsize=figsize)

        # Plot line graph
        ax.plot(sequences, latencies, marker='o', linestyle='-', linewidth=1.5,
                markersize=4, color='#2E86AB', alpha=0.7, label='Latency')

        # Add min/max/avg lines
        ax.axhline(y=stats['min'], color='green', linestyle='--', linewidth=1, alpha=0.5, label=f"Min: {stats['min']:.2f}ms")
        ax.axhline(y=stats['max'], color='red', linestyle='--', linewidth=1, alpha=0.5, label=f"Max: {stats['max']:.2f}ms")
        ax.axhline(y=stats['avg'], color='orange', linestyle='--', linewidth=1, alpha=0.5, label=f"Avg: {stats['avg']:.2f}ms")

        # Labels and title
        ax.set_xlabel('Packet Sequence', fontsize=12, fontweight='bold')
        ax.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
        title = f"Ping Latency to {self.host}"
        if stats['lost'] > 0:
            title += f" ({stats['lost']} packets lost)"
        ax.set_title(title, fontsize=14, fontweight='bold')

        # Grid and legend
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)

        # Tight layout
        plt.tight_layout()

        # Save figure
        plt.savefig(output_file, dpi=100, bbox_inches='tight')
        plt.close()

        return output_file


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Visualize ping latency as a graph")
    parser.add_argument("host", help="Host to ping")
    parser.add_argument("-c", "--count", type=int, default=100, help="Number of ping packets (default: 100)")
    parser.add_argument("-i", "--interval", type=float, default=0.1, help="Interval between packets in seconds (default: 0.1)")
    parser.add_argument("-s", "--size", type=int, default=1400, help="Packet size in bytes (default: 1400)")
    parser.add_argument("--format", choices=["ascii", "json", "csv", "image"], default="ascii", help="Output format (default: ascii)")
    parser.add_argument("--height", type=int, default=20, help="Graph height for ASCII output (default: 20)")
    parser.add_argument("--width", type=int, default=80, help="Graph width for ASCII output (default: 80)")
    parser.add_argument("-o", "--output", type=str, help="Output file path (for image format)")
    parser.add_argument("--figsize", type=str, default="12,6", help="Figure size for image output as 'width,height' (default: 12,6)")

    args = parser.parse_args()

    plotter = PingPlotter(args.host, args.count, args.interval, args.size)

    print(f"Pinging {args.host} ({args.count} packets)...", file=sys.stderr)
    if not plotter.run_ping():
        sys.exit(1)

    if args.format == "ascii":
        print(plotter.plot_ascii(args.height, args.width))
    elif args.format == "json":
        print(plotter.to_json())
    elif args.format == "csv":
        print(plotter.to_csv())
    elif args.format == "image":
        try:
            output_file = args.output or f"pingplot_{args.host.replace('.', '_')}.png"
            figsize = tuple(map(int, args.figsize.split(',')))
            result_file = plotter.plot_matplotlib(output_file, figsize)
            print(f"Graph saved to: {result_file}", file=sys.stderr)
            print(result_file)
        except ImportError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

