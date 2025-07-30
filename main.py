from fastapi import FastAPI
import yfinance as yf
from datetime import datetime
import os
import json

app = FastAPI()

@app.get("/price")
def get_price(symbol: str):
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        price = info.get("regularMarketPrice")
        currency = info.get("currency", "USD")
        return {
            "symbol": symbol.upper(),
            "price": price,
            "currency": currency
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/fundamentals")
def get_fundamentals(symbol: str):
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info

        financials = ticker.financials
        cashflow = ticker.cashflow

        latest_year = financials.columns[0] if not financials.empty else None
        if not latest_year:
            return {"error": "Keine Finanzdaten gefunden."}

        revenue = financials.loc["Total Revenue"].get(latest_year, None)
        net_income = financials.loc["Net Income"].get(latest_year, None)

        operating_cash = cashflow.loc["Total Cash From Operating Activities"].get(latest_year) \
            if "Total Cash From Operating Activities" in cashflow.index else None
        capex = cashflow.loc["Capital Expenditures"].get(latest_year) \
            if "Capital Expenditures" in cashflow.index else None

        free_cash_flow = operating_cash - capex if (operating_cash and capex) else None

        return {
            "symbol": symbol.upper(),
            "year": latest_year.year,
            "revenue": int(revenue) if revenue else None,
            "net_income": int(net_income) if net_income else None,
            "free_cash_flow": int(free_cash_flow) if free_cash_flow else None
        }

    except Exception as e:
        return {"error": str(e)}
        
@app.get("/analyze")
def analyze(symbol: str, currency: str = "EUR"):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        cashflow = ticker.cashflow
        financials = ticker.financials
        latest_year = financials.columns[0]

        # --- Umsatz & Gewinn ---
        revenue = financials.loc["Total Revenue"].get(latest_year, None) if "Total Revenue" in financials.index else None
        net_income = financials.loc["Net Income"].get(latest_year, None) if "Net Income" in financials.index else None

        # --- Operating Cash Flow ---
        op_cash_labels = [
            "Operating Cash Flow",
            "Cash Flow From Continuing Operating Activities",
            "Net Cash Provided By Operating Activities",
            "Total Cash From Operating Activities"
        ]
        op_cash = None
        op_cash_label_used = None
        for label in op_cash_labels:
            if label in cashflow.index:
                op_cash = cashflow.loc[label].get(latest_year)
                op_cash_label_used = label
                break

        # --- Capital Expenditures ---
        capex_labels = [
            "Capital Expenditures",
            "Purchase Of Property Plant And Equipment"
        ]
        capex = None
        capex_label_used = None
        for label in capex_labels:
            if label in cashflow.index:
                capex = cashflow.loc[label].get(latest_year)
                capex_label_used = label
                break

        # --- FCF & Bewertung ---
        free_cash_flow = op_cash - capex if op_cash is not None and capex is not None else None

        r = 0.08  # Discount Rate
        g = 0.05  # Growth
        fair_value = round(free_cash_flow * (1 + g) / (r - g), 2) if free_cash_flow else None

        market_price = info.get("regularMarketPrice", None)
        mos_price = round(fair_value * 0.7, 2) if fair_value else None
        verdict = (
            "Unterbewertet" if market_price and mos_price and market_price < mos_price
            else "Überbewertet" if market_price and mos_price and market_price > mos_price
            else "Unklar"
        )

        # --- Analyse als Text ---
        today = datetime.today().date()
        analysis_text = f"""# Analyse: {symbol.upper()} ({today})
**Aktueller Kurs**: {market_price} {currency}
**Fairer Wert (DCF)**: {fair_value} {currency}
**Margin of Safety (30%)**: {mos_price} {currency}

**Free Cash Flow**: {free_cash_flow}
**Umsatz**: {revenue}
**Net Income**: {net_income}

**FCF-Basis**:
- Operating Cash: {op_cash} ({op_cash_label_used})
- CapEx: {capex} ({capex_label_used})

🧠 Bewertung: {verdict}
"""

        # --- Speichern als Markdown ---
        folder = "analysen"
        os.makedirs(folder, exist_ok=True)
        filename = f"{folder}/{symbol.lower()}-{today}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(analysis_text)

        # --- Rückgabe als JSON ---
        return {
            "symbol": symbol.upper(),
            "price": market_price,
            "fair_value": fair_value,
            "mos_price": mos_price,
            "free_cash_flow": free_cash_flow,
            "net_income": net_income,
            "revenue": revenue,
            "verdict": verdict,
            "used_labels": {
                "op_cash": op_cash_label_used,
                "capex": capex_label_used
            },
            "file_saved": filename
        }

    except Exception as e:
        return {"error": str(e)}
