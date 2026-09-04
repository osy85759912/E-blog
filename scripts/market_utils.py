#!/usr/bin/env python3
"""Shared ticker/market helpers used by both generate_chart.py and
generate_thumbnail.py, so currency formatting and company-name lookups
never drift out of sync between the two."""
import sys
from datetime import datetime, timedelta

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

# yfinance's shortName for US tickers is the formal English corporate name
# (e.g. "NVIDIA Corporation"), which reads oddly on a Korean-language
# thumbnail. Override with the commonly used Korean name for frequently
# covered large caps; anything not listed falls back to yfinance.
US_KOREAN_NAMES = {
    "NVDA": "엔비디아",
    "AAPL": "애플",
    "MSFT": "마이크로소프트",
    "GOOGL": "구글",
    "GOOG": "구글",
    "AMZN": "아마존",
    "META": "메타",
    "TSLA": "테슬라",
    "AVGO": "브로드컴",
    "AMD": "AMD",
    "NFLX": "넷플릭스",
    "SMCI": "슈퍼마이크로",
    "INTC": "인텔",
    "QCOM": "퀄컴",
    "TSM": "TSMC",
    "MU": "마이크론",
    "PLTR": "팔란티어",
    "COIN": "코인베이스",
    "ORCL": "오라클",
    "CRM": "세일즈포스",
    "ADBE": "어도비",
    "UBER": "우버",
    "BA": "보잉",
    "JPM": "JP모건",
    "V": "비자",
    "MA": "마스터카드",
    "DIS": "디즈니",
    "KO": "코카콜라",
    "PEP": "펩시코",
    "WMT": "월마트",
    "COST": "코스트코",
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
    if ticker in US_KOREAN_NAMES:
        return US_KOREAN_NAMES[ticker]
    try:
        info = yf.Ticker(ticker).info
        return info.get("shortName") or info.get("longName") or ticker
    except Exception as exc:
        print(f"[market_utils] company_name_for_ticker({ticker}) failed: {exc!r}", file=sys.stderr)
        return ticker


def fetch_percent_change(ticker, as_of=None):
    """% change vs the previous trading day. With `as_of` (a date or
    YYYY-MM-DD string), this is the change AS OF THAT DAY -- not whatever
    day the script happens to run on -- so regenerating a thumbnail for an
    old post doesn't silently overwrite its number with today's move."""
    try:
        if as_of:
            if isinstance(as_of, str):
                as_of = datetime.strptime(as_of, "%Y-%m-%d").date()
            # wide start margin to clear weekends/holidays back to the prior
            # trading day; filter (rather than rely on yfinance's `end`) so
            # we never pick up a day after as_of.
            start = as_of - timedelta(days=12)
            end = as_of + timedelta(days=1)
            hist = yf.Ticker(ticker).history(start=start.isoformat(), end=end.isoformat())["Close"]
            hist = hist[hist.index.date <= as_of]
        else:
            hist = yf.Ticker(ticker).history(period="5d")["Close"]
        if len(hist) < 2:
            return None
        last, prev = hist.iloc[-1], hist.iloc[-2]
        return (last - prev) / prev * 100
    except Exception as exc:
        print(f"[market_utils] fetch_percent_change({ticker}, as_of={as_of}) failed: {exc!r}", file=sys.stderr)
        return None
