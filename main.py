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

        # Extrahiere relevante Werte
        latest_year = financials.columns[0]
        revenue = financials.loc["Total Revenue"].get(latest_year, None)
        net_income = financials.loc["Net Income"].get(latest_year, None)
        operating_cash = cashflow.loc["Total Cash From Operating Activities"].get(latest_year, None) if "Total Cash From Operating Activities" in cashflow.index else None
        capex = cashflow.loc["Capital Expenditures"].get(latest_year, None) if "Capital Expenditures" in cashflow.index else None
        free_cash_flow = operating_cash - capex if operating_cash and capex else None

        # DCF: einfache Formel → DCF = FCF * (1 + g) / (r - g)
        r = 0.08  # Discount Rate
        g = 0.05  # Growth Rate
        fair_value = round(free_cash_flow * (1 + g) / (r - g), 2) if free_cash_flow else None

        market_price = info.get("regularMarketPrice", None)
        margin_of_safety_price = round(fair_value * 0.7, 2) if fair_value else None
        overvalued = market_price > margin_of_safety_price if market_price and margin_of_safety_price else None

        # Text-Report
        analysis_text = f"""# Analyse: {symbol.upper()} ({datetime.today().date()})

**Aktueller Kurs**: {market_price} {currency}
**Fairer Wert (DCF)**: {fair_value} {currency}
**Margin of Safety (30%)**: {margin_of_safety_price} {currency}

**Free Cash Flow**: {free_cash_flow}
**Umsatz**: {revenue}
**Net Income**: {net_income}

Bewertung: {"❌ Überbewertet" if overvalued else "✅ Unterbewertet" if overvalued == False else "– Keine Bewertung möglich"}
        """

        # Speichern
        folder = "analysen"
        os.makedirs(folder, exist_ok=True)
        filename = f"{folder}/{symbol.lower()}-{datetime.today().date()}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(analysis_text)

        return {
            "symbol": symbol.upper(),
            "price": market_price,
            "fair_value": fair_value,
            "mos_price": margin_of_safety_price,
            "free_cash_flow": free_cash_flow,
            "net_income": net_income,
            "revenue": revenue,
            "verdict": "Unterbewertet" if overvalued == False else "Überbewertet" if overvalued else "Unklar",
            "file_saved": filename
        }

    except Exception as e:
        return {"error": str(e)}
