from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "KR7Sclg6pbBPdSFHkwyz3czQpCKOzP6ppszkWFROU8kvM0QdV7XaQ6A7bqDOX27qiZCxBCLA6VWa+Ke85Ekni+Fxwi7vasS9dz4+q5KRVfbIN2uhF2XCSrLaJlsOeQAsnQDUE6O7tFyEZemn72DccAdB04t89/1O/w1cDnyilFU="
USER_FILE = "users.json"

@app.route("/callback", methods=["POST"])

def load_users():
    if not os.path.exists(USER_FILE): 
        return {}
    with open(USER_FILE, "r", encoding= "utf-8") as f:
        return json.load(f)


def add_users(user_id):
    users = load_users()
    users[user_id] = {
        "name": "unknown",
        "class": "unknown"
    }
    with open(USER_FILE, "w", encoding= "utf-8") as f:
        json.dump(users, f, ensure_ascii= False, indent= 2)

def callback():
    data = request.get_json()
    print(data, flush=True)  # Webhook届いたか確認用

    # イベント取得（複数イベントが来る可能性あり）
    for event in data.get("events", []):
        reply_token = event["replyToken"]
        user_id = event["source"]["userId"]
        users = load_users()

        if user_id not in users:
            reply_message(reply_token, "adding user infomation")
            add_users(user_id)
            return("OK")
        else:
            reply_message(reply_token, "auto_reply run successfully")
            return("OK")

def reply_message(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "replyToken": reply_token,
        "messages": [
            {"type": "text", "text": text}
        ]
    }
    requests.post(url, headers=headers, data=json.dumps(body))