from fastapi import FastAPI
import requests

app = FastAPI()

API_KEY = "6h6GDJbniaGPJ1X0zZPeFQXQaMWhojyu"
HEADERS = {"User-Agent": "Mozilla/5.0"}  # WICHTIG für Render!

def get_fx_rate():
    fx_url = f"https://financialmodelingprep.com/stable/quote-short?symbol=EURUSD&apikey={API_KEY}"
    try:
        resp = requests.get(fx_url, headers=HEADERS)
        data = resp.json()
        return data[0]["price"]
    except Exception as e:
        print("FX-Fehler:", str(e))
        return 1.0


@app.get("/price")
def get_price(symbol: str, currency: str = "EUR"):
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol.upper()},EURUSD?apikey={API_KEY}"
        response = requests.get(url, headers=HEADERS)
        data = response.json()

        if not data or len(data) < 2:
            return {"error": "Kursdaten unvollständig.", "response": data}

        stock_data = next((d for d in data if d["symbol"] == symbol.upper()), None)
        fx_data = next((d for d in data if d["symbol"] == "EURUSD"), None)

        if not stock_data or not fx_data:
            return {"error": "Fehlende Daten im Ergebnis."}

        price_usd = stock_data["price"]
        eur_usd = fx_data["price"]
        fx_rate = round(1 / eur_usd, 6)
        price = round(price_usd * fx_rate, 2)

        return {
            "symbol": symbol.upper(),
            "price": price,
            "currency": currency.upper(),
            "converted_from": "USD",
