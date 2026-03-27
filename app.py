from flask import Flask, request
import requests

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print(data)
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "bot working"