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

        financials = ticker.financials  # Gewinn & Umsatz
        cashflow = ticker.cashflow      # Free Cashflow

        latest_year = financials.columns[0] if not financials.empty else None
        if not latest_year:
            return {"error": "Keine Finanzdaten gefunden."}

        revenue = financials.loc["Total Revenue"][latest_year]
        net_income = financials.loc["Net Income"][latest_year]
        free_cash_flow = cashflow.loc["Total Cash From Operating Activities"][latest_year] - \
                         cashflow.loc["Capital Expenditures"][latest_year]

        return {
            "symbol": symbol.upper(),
            "year": latest_year.year,
            "revenue": int(revenue),
            "net_income": int(net_income),
            "free_cash_flow": int(free_cash_flow)
        }
    except Exception as e:
        return {"error": str(e)}
