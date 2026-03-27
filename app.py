from flask import Flask, request
import requests
import os
import json


#АПИ бота
TOKEN = "7805213873:AAEL0F__2PFPyh21q9eYRxrzBPBsg-WPRIM"
#ссылка на канал
CHANNEL_URL = "https://t.me/+YIBGmH8XuzVjNzJi"

URL = f"https://api.telegram.org/bot{TOKEN}"
app = Flask(__name__)

# Временное хранилище состояний пользователей.
# Для старта подходит. Позже можно вынести в базу.
users = {}


def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    response = requests.post(f"{URL}/sendMessage", json=payload, timeout=15)
    return response.json()


def send_channel_button(chat_id):
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "Вступить в канал",
                    "url": CHANNEL_URL
                }
            ]
        ]
    }

    send_message(
        chat_id,
        "Спасибо! Доступ почти готов.\n\nНажмите кнопку ниже, чтобы перейти в канал:",
        reply_markup=keyboard
    )


def age_keyboard():
    return {
        "keyboard": [
            ["до 1 года"],
            ["1-2 года"],
            ["2-3 года"],
            ["3+"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }


def problem_keyboard():
    return {
        "keyboard": [
            ["не говорит"],
            ["мало слов"],
            ["не понимает"],
            ["хочу развитие"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }


def contact_keyboard():
    return {
        "keyboard": [
            [
                {
                    "text": "Отправить номер",
                    "request_contact": True
                }
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }


def remove_keyboard():
    return {
        "remove_keyboard": True
    }


def log_lead(chat_id):
    user = users.get(chat_id, {})
    print("========== НОВЫЙ ЛИД ==========")
    print(json.dumps({
        "chat_id": chat_id,
        "name": user.get("name"),
        "age": user.get("age"),
        "problem": user.get("problem"),
        "phone": user.get("phone")
    }, ensure_ascii=False, indent=2))
    print("================================")


@app.route("/", methods=["GET"])
def home():
    return "bot working", 200


@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    print("==== TELEGRAM UPDATE ====")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("=========================")

    if not data:
        return "ok", 200

    if "message" not in data:
        return "ok", 200

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if chat_id not in users:
        users[chat_id] = {"step": "name"}

    # старт
    if text == "/start":
        users[chat_id] = {"step": "name"}
        send_message(
            chat_id,
            "Здравствуйте! Ответьте на 3 вопроса и получите доступ к каналу.\n\nКак вас зовут?",
            reply_markup=remove_keyboard()
        )
        return "ok", 200

    current_step = users[chat_id].get("step")

    # шаг 1: имя
    if current_step == "name":
        if not text:
            send_message(chat_id, "Напишите, пожалуйста, ваше имя.")
            return "ok", 200

        users[chat_id]["name"] = text
        users[chat_id]["step"] = "age"

        send_message(
            chat_id,
            "Возраст ребёнка?",
            reply_markup=age_keyboard()
        )
        return "ok", 200

    # шаг 2: возраст
    if current_step == "age":
        allowed_ages = {"до 1 года", "1-2 года", "2-3 года", "3+"}
        if text not in allowed_ages:
            send_message(
                chat_id,
                "Выберите возраст ребёнка кнопкой ниже.",
                reply_markup=age_keyboard()
            )
            return "ok", 200

        users[chat_id]["age"] = text
        users[chat_id]["step"] = "problem"

        send_message(
            chat_id,
            "Что вас беспокоит больше всего?",
            reply_markup=problem_keyboard()
        )
        return "ok", 200

    # шаг 3: проблема
    if current_step == "problem":
        allowed_problems = {"не говорит", "мало слов", "не понимает", "хочу развитие"}
        if text not in allowed_problems:
            send_message(
                chat_id,
                "Выберите вариант кнопкой ниже.",
                reply_markup=problem_keyboard()
            )
            return "ok", 200

        users[chat_id]["problem"] = text
        users[chat_id]["step"] = "phone"

        send_message(
            chat_id,
            "Оставьте номер телефона, чтобы получить доступ.",
            reply_markup=contact_keyboard()
        )
        return "ok", 200

    # шаг 4: телефон
    if current_step == "phone":
        if "contact" in message:
            phone = message["contact"].get("phone_number", "")
            users[chat_id]["phone"] = phone
            users[chat_id]["step"] = "done"

            log_lead(chat_id)

            send_message(
                chat_id,
                "Спасибо! Анкета заполнена.",
                reply_markup=remove_keyboard()
            )
            send_channel_button(chat_id)
            return "ok", 200

        send_message(
            chat_id,
            "Пожалуйста, нажмите кнопку «Отправить номер».",
            reply_markup=contact_keyboard()
        )
        return "ok", 200

    # если уже всё заполнено
    if users[chat_id].get("step") == "done":
        send_channel_button(chat_id)
        return "ok", 200

    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
