from flask import Flask, request
import requests
import os
import json

# =========================
# TELEGRAM
# =========================

#АПИ бота
TOKEN = "7805213873:AAEL0F__2PFPyh21q9eYRxrzBPBsg-WPRIM"
#ссылка на канал
CHANNEL_URL = "https://t.me/+YIBGmH8XuzVjNzJi"
TG_URL = f"https://api.telegram.org/bot{TOKEN}"

# =========================
# AMOCRM
# =========================
SUBDOMAIN = "sugraliev"
ACCESS_TOKEN = "ВСТАВЬ_ACCESS_TOKEN"
BASE_AMO_URL = f"https://{SUBDOMAIN}.amocrm.ru"

PIPELINE_ID = 10718634
STATUS_ID = 84442662

CF_AGE = 3799411
CF_PROBLEM = 3799407
CF_SOURCE = 3799409

app = Flask(__name__)
users = {}


# =========================
# TELEGRAM HELPERS
# =========================
def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    response = requests.post(f"{TG_URL}/sendMessage", json=payload, timeout=20)
    print("TG SEND:", response.status_code, response.text)
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
        "Спасибо! Заявка принята.\n\nНажмите кнопку ниже, чтобы перейти в канал.",
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


# =========================
# AMOCRM HELPERS
# =========================
def amo_headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }


def create_amo_lead(user):
    url = f"{BASE_AMO_URL}/api/v4/leads/complex"

    payload = [
        {
            "name": f"Telegram | {user['name']}",
            "pipeline_id": PIPELINE_ID,
            "status_id": STATUS_ID,
            "_embedded": {
                "contacts": [
                    {
                        "first_name": user["name"],
                        "custom_fields_values": [
                            {
                                "field_code": "PHONE",
                                "values": [
                                    {
                                        "value": user["phone"],
                                        "enum_code": "WORK"
                                    }
                                ]
                            },
                            {
                                "field_id": CF_AGE,
                                "values": [
                                    {
                                        "value": user["age"]
                                    }
                                ]
                            },
                            {
                                "field_id": CF_PROBLEM,
                                "values": [
                                    {
                                        "value": user["problem"]
                                    }
                                ]
                            },
                            {
                                "field_id": CF_SOURCE,
                                "values": [
                                    {
                                        "value": "Telegram бот"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    ]

    response = requests.post(url, headers=amo_headers(), json=payload, timeout=25)
    print("AMO STATUS:", response.status_code)
    print("AMO RESPONSE:", response.text)
    response.raise_for_status()
    return response.json()


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


# =========================
# ROUTES
# =========================
@app.route("/", methods=["GET"])
def home():
    return "bot working", 200


@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    print("==== TELEGRAM UPDATE ====")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("=========================")

    if not data or "message" not in data:
        return "ok", 200

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if chat_id not in users:
        users[chat_id] = {"step": "name"}

    if text == "/start":
        users[chat_id] = {"step": "name"}
        send_message(
            chat_id,
            "Здравствуйте! Ответьте на 3 вопроса и получите доступ к каналу.\n\nКак вас зовут?",
            reply_markup=remove_keyboard()
        )
        return "ok", 200

    current_step = users[chat_id].get("step")

    if current_step == "name":
        if not text:
            send_message(chat_id, "Напишите, пожалуйста, ваше имя.")
            return "ok", 200

        users[chat_id]["name"] = text
        users[chat_id]["step"] = "age"

        send_message(
            chat_id,
            "Сколько лет ребенку?",
            reply_markup=age_keyboard()
        )
        return "ok", 200

    if current_step == "age":
        allowed_ages = {"до 1 года", "1-2 года", "2-3 года", "3+"}
        if text not in allowed_ages:
            send_message(
                chat_id,
                "Выберите возраст кнопкой ниже.",
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

    if current_step == "phone":
        if "contact" in message:
            phone = message["contact"].get("phone_number", "")
            users[chat_id]["phone"] = phone
            users[chat_id]["step"] = "done"

            log_lead(chat_id)

            try:
                create_amo_lead(users[chat_id])
                send_message(
                    chat_id,
                    "Спасибо! Анкета заполнена.",
                    reply_markup=remove_keyboard()
                )
                send_channel_button(chat_id)
            except Exception as e:
                print("AMOCRM ERROR:", str(e))
                send_message(
                    chat_id,
                    "Анкета принята, но произошла ошибка при передаче данных. Напишите администратору.",
                    reply_markup=remove_keyboard()
                )

            return "ok", 200

        send_message(
            chat_id,
            "Пожалуйста, нажмите кнопку «Отправить номер».",
            reply_markup=contact_keyboard()
        )
        return "ok", 200

    if users[chat_id].get("step") == "done":
        send_channel_button(chat_id)
        return "ok", 200

    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
