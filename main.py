from fastapi import FastAPI
import yfinance as yf

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
