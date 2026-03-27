from flask import Flask, request
import requests
import os

TOKEN = "7805213873:AAEL0F__2PFPyh21q9eYRxrzBPBsg-WPRIM"
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

def send_message(chat_id, text):
    requests.post(f"{URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if "message" not in data:
        return "ok"

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if text == "/start":
        send_message(chat_id,
        "Здравствуйте! Ответьте на 3 вопроса и получите доступ к каналу\n\nКак вас зовут?")
    else:
        send_message(chat_id, "Спасибо! Я записал.")

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "bot working"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
