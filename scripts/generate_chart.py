#!/usr/bin/env python3
import argparse
import os
import sys

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import yfinance as yf

matplotlib.use("Agg")

COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed"]
KRW_SUFFIXES = (".KS", ".KQ")

# yfinance's shortName/longName for KRX tickers is an English abbreviation
# (e.g. "SK hynix", "SamsungElec"), not the Korean name a domestic-market
# reader expects. Override with the real Korean name for common large caps;
# anything not listed here falls back to whatever yfinance returns.
KRX_KOREAN_NAMES = {
    "005930.KS": "삼성전자",
    "000660.KS": "SK하이닉스",
    "373220.KS": "LG에너지솔루션",
    "207940.KS": "삼성바이오로직스",
    "005380.KS": "현대차",
    "000270.KS": "기아",
    "068270.KS": "셀트리온",
    "005490.KS": "POSCO홀딩스",
    "035420.KS": "NAVER",
    "035720.KS": "카카오",
    "051910.KS": "LG화학",
    "006400.KS": "삼성SDI",
    "105560.KS": "KB금융",
    "055550.KS": "신한지주",
    "086790.KS": "하나금융지주",
    "012450.KS": "한화에어로스페이스",
    "028260.KS": "삼성물산",
    "012330.KS": "현대모비스",
    "066570.KS": "LG전자",
    "096770.KS": "SK이노베이션",
    "034020.KS": "두산에너빌리티",
    "259960.KS": "크래프톤",
    "323410.KS": "카카오뱅크",
    "032830.KS": "삼성생명",
    "034730.KS": "SK",
    "003550.KS": "LG",
    "015760.KS": "한국전력",
    "316140.KS": "우리금융지주",
    "138040.KS": "메리츠금융지주",
    "000810.KS": "삼성화재",
    "010130.KS": "고려아연",
    "033780.KS": "KT&G",
    "329180.KS": "HD현대중공업",
    "042700.KS": "한미반도체",
    "004990.KS": "롯데지주",
    "011200.KS": "HMM",
    "010950.KS": "S-Oil",
    "000720.KS": "현대건설",
    "196170.KQ": "알테오젠",
    "222800.KQ": "심텍",
    "240810.KQ": "원익IPS",
    "036930.KQ": "주성엔지니어링",
    "086520.KQ": "에코프로",
    "247540.KQ": "에코프로비엠",
    "028300.KQ": "HLB",
}

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


def is_krw_ticker(ticker):
    return ticker.upper().endswith(KRW_SUFFIXES)


def currency_unit(ticker):
    return "원" if is_krw_ticker(ticker) else "$"


def company_name_for_ticker(ticker):
    ticker = ticker.upper()
    if ticker in KRX_KOREAN_NAMES:
        return KRX_KOREAN_NAMES[ticker]
    try:
        info = yf.Ticker(ticker).info
        return info.get("shortName") or info.get("longName") or ticker
    except Exception as exc:
        print(f"[chart] company_name_for_ticker({ticker}) failed: {exc!r}", file=sys.stderr)
        return ticker


def krw_formatter(value, _pos):
    return f"{value:,.0f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", required=True, help="comma-separated, e.g. NVDA,SMCI")
    parser.add_argument("--period", default="6mo")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if not tickers:
        sys.exit("no tickers given")

    names = {t: company_name_for_ticker(t) for t in tickers}

    data = yf.download(tickers, period=args.period, auto_adjust=True, progress=False)["Close"]
    if data.empty:
        sys.exit(f"no price data returned for {tickers}")

    columns = list(data.columns) if hasattr(data, "columns") else [tickers[0]]

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)

    if len(columns) <= 1:
        ticker = columns[0]
        series = data[ticker] if hasattr(data, "columns") else data
        ax.plot(series.index, series.values, color=COLORS[0], linewidth=2)
        ax.set_ylabel(f"{names[ticker]} 주가 ({currency_unit(ticker)})")
        if is_krw_ticker(ticker):
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(krw_formatter))
        lines, labels = ax.get_legend_handles_labels()
    elif len(columns) == 2:
        t0, t1 = columns[0], columns[1]
        ax2 = ax.twinx()
        ax2.spines["top"].set_visible(False)
        series0, series1 = data[t0], data[t1]
        line0, = ax.plot(series0.index, series0.values, label=names[t0], color=COLORS[0], linewidth=2)
        line1, = ax2.plot(series1.index, series1.values, label=names[t1], color=COLORS[1], linewidth=2)
        ax.set_ylabel(f"{names[t0]} 주가 ({currency_unit(t0)})", color=COLORS[0])
        ax2.set_ylabel(f"{names[t1]} 주가 ({currency_unit(t1)})", color=COLORS[1])
        ax.tick_params(axis="y", labelcolor=COLORS[0])
        ax2.tick_params(axis="y", labelcolor=COLORS[1])
        if is_krw_ticker(t0):
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(krw_formatter))
        if is_krw_ticker(t1):
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(krw_formatter))
        lines, labels = [line0, line1], [names[t0], names[t1]]
    else:
        for i, ticker in enumerate(columns):
            series = data[ticker]
            label = f"{names[ticker]} ({currency_unit(ticker)})"
            ax.plot(series.index, series.values, label=label, color=COLORS[i % len(COLORS)], linewidth=2)
        ax.set_ylabel("주가")
        lines, labels = ax.get_legend_handles_labels()

    ax.set_title(f"{args.period} 주가 추이", fontsize=13, pad=12)
    if labels:
        ax.legend(lines, labels, loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig(args.out)
    print(args.out)


if __name__ == "__main__":
    main()
