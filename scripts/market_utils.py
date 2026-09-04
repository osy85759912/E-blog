#!/usr/bin/env python3
"""Shared ticker/market helpers used by both generate_chart.py and
generate_thumbnail.py, so currency formatting and company-name lookups
never drift out of sync between the two."""
import sys

import yfinance as yf

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

# index ticker + display label, per market. Order matters -- first entry is
# the "hero" index (KOSPI / S&P500), second is secondary (KOSDAQ / Nasdaq).
INDEX_TICKERS = {
    "kr": [("^KS11", "코스피"), ("^KQ11", "코스닥")],
    "us": [("^GSPC", "S&P500"), ("^IXIC", "나스닥")],
}


def market_for_category(category):
    return "kr" if category == "국내주식" else "us"


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
        print(f"[market_utils] company_name_for_ticker({ticker}) failed: {exc!r}", file=sys.stderr)
        return ticker


def fetch_percent_change(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="5d")["Close"]
        if len(hist) < 2:
            return None
        last, prev = hist.iloc[-1], hist.iloc[-2]
        return (last - prev) / prev * 100
    except Exception as exc:
        print(f"[market_utils] fetch_percent_change({ticker}) failed: {exc!r}", file=sys.stderr)
        return None
