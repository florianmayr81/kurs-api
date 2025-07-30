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
        fx_rate = get_fx_rate(currency)
        return {
            "symbol": symbol.upper(),
            "price": round(price_usd * fx_rate, 2),
            "currency": currency
        }
    except Exception as e:
        return {"error": str(e)}
