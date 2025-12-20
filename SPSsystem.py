from flask import Flask, request
import requests
import json

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "KR7Sclg6pbBPdSFHkwyz3czQpCKOzP6ppszkWFROU8kvM0QdV7XaQ6A7bqDOX27qiZCxBCLA6VWa+Ke85Ekni+Fxwi7vasS9dz4+q5KRVfbIN2uhF2XCSrLaJlsOeQAsnQDUE6O7tFyEZemn72DccAdB04t89/1O/w1cDnyilFU="

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    print(data, flush=True)  # Webhook届いたか確認

    #　イベント取得（複数イベントが来る可能性あり）
    for event in data.get("events", []):
        chat_id = event.get("source", {}).get("chatId")
        reply_token = event.get("replyToken")

        if chat_id:
            start_loading(chat_id)

        if reply_token:
            reply_message(reply_token, "自動返信テスト成功")

    return "OK"

def start_loading(chat_id):
    url = "https://api.line.me/v2/bot/chat/loading/start"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "chatId": chat_id,
        "loadingSeconds": 5
    }
    requests.post(url, headers=headers, data=json.dumps(body))

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