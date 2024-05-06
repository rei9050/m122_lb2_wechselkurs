from flask import Flask, render_template, request
import requests
import logging
import config

app = Flask(__name__)

# Konfiguration des Loggers
logging.basicConfig(filename='currency_converter.log', level=logging.INFO)


# Funktion zum Abrufen der Wechselkurse von der API nur für CHF
def get_exchange_rates(api_key):
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/CHF"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("conversion_rates")
    except requests.RequestException as e:
        error_message = f"Fehler beim Abrufen der Wechselkurse von der API: {str(e)}"
        logging.warning(error_message)
        return None


# Funktion zur Währungsumrechnung
def convert_currency(amount, from_currency, to_currency, exchange_rates):
    if from_currency == to_currency:
        error_message = "Die Ausgangs- und Zielwährungen sind identisch."
        logging.warning(error_message)
        return None

    if from_currency not in exchange_rates or to_currency not in exchange_rates:
        error_message = f"Ungültige Währung(en) verwendet: von {from_currency} zu {to_currency}"
        logging.warning(error_message)
        return None

    conversion_rate = exchange_rates[to_currency] / exchange_rates[from_currency]
    converted_amount = amount * conversion_rate
    return converted_amount


# Funktion zum Protokollieren von Aktivitäten
def log_activity(message):
    logging.info(message)


# Liste für die Speicherung der Umrechnungshistorie
conversion_history = []


# Hauptfunktion
@app.route("/", methods=["GET", "POST"])
def main():
    # Abrufen der Umrechnungskurse nur für CHF
    api_key = config.EXCHANGE_RATE_API_KEY
    exchange_rates = get_exchange_rates(api_key)

    # Liste der 20 verschiedenen Währungen
    currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CNY", "INR", "SGD", "CHF",
                  "MYR", "NZD", "THB", "ZAR", "HKD", "SEK", "NOK", "MXN", "DKK", "RUB"]

    # Umrechnungen von 1 CHF in 20 verschiedene Währungen
    conversions = []
    if exchange_rates:
        for currency in currencies:
            if currency in exchange_rates:
                conversion_rate = exchange_rates[currency]
                conversions.append((1, "CHF", conversion_rate, currency))

    if request.method == "POST":
        amount = request.form.get("amount", type=float)
        from_currency = request.form.get("from_currency", "").upper()
        to_currency = request.form.get("to_currency", "").upper()

        if exchange_rates:
            converted_amount = convert_currency(amount, from_currency, to_currency, exchange_rates)
            if converted_amount is not None:
                log_activity(f"{amount} {from_currency} entspricht {converted_amount} {to_currency}.")
                conversion_history.append((amount, from_currency, converted_amount, to_currency))
                return render_template("result.html", amount=amount, from_currency=from_currency,
                                       converted_amount=converted_amount, to_currency=to_currency)
            else:
                error_message = "Die Umrechnung konnte nicht durchgeführt werden."
                logging.warning(error_message)
                return render_template("error.html", error_message=error_message)

    return render_template("index.html", conversions=conversions)


# Route für die Anzeige der Umrechnungshistorie
@app.route("/history")
def history():
    return render_template("history.html", conversion_history=conversion_history)


if __name__ == "__main__":
    app.run(debug=True)
