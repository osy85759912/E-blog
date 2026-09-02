#!/usr/bin/env python3
import argparse
import os
import sys

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import yfinance as yf

matplotlib.use("Agg")

COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed"]

KOREAN_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]
for _font_path in KOREAN_FONT_CANDIDATES:
    if os.path.exists(_font_path):
        fm.fontManager.addfont(_font_path)
        plt.rcParams["font.family"] = fm.FontProperties(fname=_font_path).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", required=True, help="comma-separated, e.g. NVDA,SMCI")
    parser.add_argument("--period", default="6mo")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if not tickers:
        sys.exit("no tickers given")

    data = yf.download(tickers, period=args.period, auto_adjust=True, progress=False)["Close"]
    if data.empty:
        sys.exit(f"no price data returned for {tickers}")

    columns = list(data.columns) if hasattr(data, "columns") else [tickers[0]]

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)

    if len(columns) <= 1:
        series = data[columns[0]] if hasattr(data, "columns") else data
        ax.plot(series.index, series.values, color=COLORS[0], linewidth=2)
        ax.set_ylabel(f"{columns[0]} 주가 ($)")
        lines, labels = ax.get_legend_handles_labels()
    elif len(columns) == 2:
        ax2 = ax.twinx()
        ax2.spines["top"].set_visible(False)
        series0, series1 = data[columns[0]], data[columns[1]]
        line0, = ax.plot(series0.index, series0.values, label=columns[0], color=COLORS[0], linewidth=2)
        line1, = ax2.plot(series1.index, series1.values, label=columns[1], color=COLORS[1], linewidth=2)
        ax.set_ylabel(f"{columns[0]} 주가 ($)", color=COLORS[0])
        ax2.set_ylabel(f"{columns[1]} 주가 ($)", color=COLORS[1])
        ax.tick_params(axis="y", labelcolor=COLORS[0])
        ax2.tick_params(axis="y", labelcolor=COLORS[1])
        lines, labels = [line0, line1], [columns[0], columns[1]]
    else:
        for i, ticker in enumerate(columns):
            series = data[ticker]
            ax.plot(series.index, series.values, label=ticker, color=COLORS[i % len(COLORS)], linewidth=2)
        ax.set_ylabel("주가 ($)")
        lines, labels = ax.get_legend_handles_labels()

    ax.set_title(f"{args.period} 주가 추이", fontsize=13, pad=12)
    if labels:
        ax.legend(lines, labels, loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig(args.out)
    print(args.out)


if __name__ == "__main__":
    main()
