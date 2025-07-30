from fastapi import FastAPI
import requests

app = FastAPI()

API_KEY = "6h6GDJbniaGPJ1X0zZPeFQXQaMWhojyu"

def get_fx_rate(to_currency="EUR"):
    fx_url = f"https://financialmodelingprep.com/api/v3/fx/USD/{to_currency}?apikey={API_KEY}"
    try:
        resp = requests.get(fx_url)
        data = resp.json()
        return data[0]["bid"]
    except:
        return 1.0

@app.get("/price")
def get_price(symbol: str, currency: str = "EUR"):
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol.upper()}?apikey={API_KEY}"
        resp = requests.get(url)
        data = resp.json()
        if not data or "price" not in data[0]:
            return {"error": "Preis nicht gefunden"}
        price_usd = data[0]["price"]
        
# Wechselkurs USD → EUR abrufen (nur wenn currency = EUR)
        if currency.upper() == "EUR":
            fx_url = f"https://financialmodelingprep.com/api/v3/fx/USD/EUR?apikey={API_KEY}"
            fx_data = requests.get(fx_url).json()
            fx_rate = fx_data[0]["bid"]
            price = round(price_usd * fx_rate, 2)
        else:
            price = price_usd
            fx_rate = 1.0

        return {
            "symbol": symbol.upper(),
            "price": price,
            "currency": currency.upper(),
            "converted_from": "USD",
            "exchange_rate_used": fx_rate
        }
    except Exception as e:
        return {"error": str(e)}
        
@app.get("/fundamentals")
def get_fundamentals(symbol: str, year: int):
    try:
        url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol.upper()}?limit=3&apikey=6h6GDJbniaGPJ1X0zZPeFQXQaMWhojyu"
        resp = requests.get(url)
        data = resp.json()

        # Suche nach dem gewünschten Jahr
        match = next((item for item in data if str(year) in item["date"]), None)
        if not match:
            return {"error": f"Kein Bericht für {symbol} im Jahr {year} gefunden."}

        revenue = match.get("revenue")
        ebit = match.get("operatingIncome")
        net_income = match.get("netIncome")
        fcf_url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{symbol.upper()}?limit=5&apikey=6h6GDJbniaGPJ1X0zZPeFQXQaMWhojyu"
        fcf_data = requests.get(fcf_url).json()
        fcf_match = next((item for item in fcf_data if str(year) in item["date"]), None)
        free_cash_flow = fcf_match.get("freeCashFlow") if fcf_match else None

        margin = round(net_income / revenue * 100, 2) if revenue and net_income else None

        return {
            "symbol": symbol.upper(),
            "year": year,
            "revenue": revenue,
            "ebit": ebit,
            "net_income": net_income,
            "free_cash_flow": free_cash_flow,
            "net_margin": margin
        }
    except Exception as e:
        return {"error": str(e)}
