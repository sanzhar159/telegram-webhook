from flask import Flask, request
import requests
import os

TOKEN = "7805213873:AAEL0F__2PFPyh21q9eYRxrzBPBsg-WPRIM"
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

users = {}

def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    requests.post(f"{URL}/sendMessage", json=data)


@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if "message" not in data:
        return "ok"

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if chat_id not in users:
        users[chat_id] = {"step": "name"}

    step = users[chat_id]["step"]

    if text == "/start":
        users[chat_id]["step"] = "name"
        send_message(chat_id, "Здравствуйте! Как вас зовут?")
        return "ok"

    if step == "name":
        users[chat_id]["name"] = text
        users[chat_id]["step"] = "age"

        keyboard = {
            "keyboard": [
                ["до 1 года"],
                ["1-2 года"],
                ["2-3 года"],
                ["3+"]
            ],
            "resize_keyboard": True
        }

        send_message(chat_id, "Возраст ребенка?", keyboard)
        return "ok"

    if step == "age":
        users[chat_id]["age"] = text
        users[chat_id]["step"] = "problem"

        keyboard = {
            "keyboard": [
                ["не говорит"],
                ["мало слов"],
                ["не понимает"],
                ["просто развитие"]
            ],
            "resize_keyboard": True
        }

        send_message(chat_id, "Что беспокоит?", keyboard)
        return "ok"

    if step == "problem":
        users[chat_id]["problem"] = text
        users[chat_id]["step"] = "phone"

        keyboard = {
            "keyboard": [
                [{
                    "text": "Отправить номер",
                    "request_contact": True
                }]
            ],
            "resize_keyboard": True
        }

        send_message(chat_id, "Отправьте номер для доступа", keyboard)
        return "ok"

    if "contact" in message:
        users[chat_id]["phone"] = message["contact"]["phone_number"]

        user = users[chat_id]

        print("НОВЫЙ ЛИД:")
        print(user)

        send_message(chat_id, "Спасибо! Доступ открыт")
        send_message(chat_id, "https://t.me/+YIBGmH8XuzVjNzJi")
        users[chat_id]["step"] = "done"

    return "ok"


@app.route("/", methods=["GET"])
def home():
    return "bot working"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
