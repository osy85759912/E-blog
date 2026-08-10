#!/usr/bin/env python3
import argparse
import sys

import matplotlib
import matplotlib.pyplot as plt
import yfinance as yf

matplotlib.use("Agg")

COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed"]


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

    normalized = data / data.iloc[0] * 100

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    columns = normalized.columns if hasattr(normalized, "columns") else [tickers[0]]
    for i, ticker in enumerate(columns):
        series = normalized[ticker] if hasattr(normalized, "columns") else normalized
        ax.plot(series.index, series.values, label=ticker, color=COLORS[i % len(COLORS)], linewidth=2)

    ax.set_title(f"{args.period} 주가 추이 (시작일 = 100)", fontsize=13, pad=12)
    ax.set_ylabel("상대 지수 (시작일=100)")
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig(args.out)
    print(args.out)


if __name__ == "__main__":
    main()
