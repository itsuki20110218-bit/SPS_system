from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "KR7Sclg6pbBPdSFHkwyz3czQpCKOzP6ppszkWFROU8kvM0QdV7XaQ6A7bqDOX27qiZCxBCLA6VWa+Ke85Ekni+Fxwi7vasS9dz4+q5KRVfbIN2uhF2XCSrLaJlsOeQAsnQDUE6O7tFyEZemn72DccAdB04t89/1O/w1cDnyilFU="
USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE): 
        return {}
    with open(USER_FILE, "r", encoding= "utf-8") as f:
        return json.load(f)


def add_users(user_id): # ユーザー情報を追加
    users = load_users()
    users[user_id] = {
        "register_status": "waiting_name",
        "name": "unknown",
        "class": "unknown",
        "service_status": "None"
    }
    with open(USER_FILE, "w", encoding= "utf-8") as f:
        json.dump(users, f, ensure_ascii= False, indent= 2)

def save_users(users): # ユーザー情報を更新
    with open(USER_FILE, "w", encoding= "utf-8") as f:
        json.dump(users, f, ensure_ascii= False, indent= 2)

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    print(data, flush=True)

    for event in data.get("events", []):

        if event["type"] != "message" or event["message"]["type"] != "text":
            continue
        
        reply_token = event["replyToken"]   # ローカル関数にしてるのはeventが来た時に使うから
        user_id = event["source"]["userId"]
        users = load_users()
        text = event["message"]["text"]

        if user_id not in users:
            reply_message(reply_token, "はじめまして。初回利用のため、ユーザー情報を登録します。\n本名を入力してください。")
            add_users(user_id)
            return "OK"
        
        else:
            register_status = users[user_id]["register_status"]
            service_status = users[user_id]["service_status"]

            if register_status == "waiting_name":
                if text == "サービスを利用":
                    reply_message(reply_token, "本名を入力してください。")
                    return "OK"
                else:
                    reply_message(reply_token, "本名を登録しました。次にクラスを入力してください。")
                    users[user_id]["register_status"] = "waiting_class"
                    users[user_id]["name"] = text
                    save_users(users)
                    return "OK"
                
            elif register_status == "waiting_class":
                if text != "A" and text != "B" and text != "C" and text != "D":
                    reply_message(reply_token, "正しいクラスを入力してください。")
                    return "OK"
                else:
                    reply_message(reply_token, "ユーザー情報の登録が完了しました。")
                    users[user_id]["register_status"] = "registered"
                    users[user_id]["class"] = text
                    save_users(users)
                    return "OK"

            elif register_status == "registered":
                if service_status == "None":
                    if text == "サービスを利用":
                        reply_message(reply_token, "科目を選択してください。\n1. 国語\n2. 数学\n3. 英語")
                        users[user_id]["service_status"] = "waiting_subject"
                        save_users(users)
                        return "OK"

                    elif service_status == "waiting_subject":
                        if text not in ["国語", "数学", "英語"]:
                            reply_message(reply_token, "利用可能な科目を選択してください。")
                            return "OK"
                        else:
                            reply_message(reply_token, text + "のプリントを送信します。")
                            users[user_id]["service_status"] = "None"
                            save_users(users)
                            return "OK"
                    
            else:
                reply_message(reply_token, "こんにちは、" + users[user_id]["name"] + "さん。\n サービスを利用する際は、画面下部の「サービスを利用」ボタンをタップしてください。")
                return "OK"

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