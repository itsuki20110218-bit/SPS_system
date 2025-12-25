from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "KR7Sclg6pbBPdSFHkwyz3czQpCKOzP6ppszkWFROU8kvM0QdV7XaQ6A7bqDOX27qiZCxBCLA6VWa+Ke85Ekni+Fxwi7vasS9dz4+q5KRVfbIN2uhF2XCSrLaJlsOeQAsnQDUE6O7tFyEZemn72DccAdB04t89/1O/w1cDnyilFU="
USER_FILE = "users.json"
ADMIN_IDS = [
    "U4eb36bd4d473ed9db5848631fbb6c47d"
    ]

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
        "service_status": "None",
        "current_subject": "None",
        "admin_status": "-",
        "admin_current_subject": "-"
    }
    with open(USER_FILE, "w", encoding= "utf-8") as f:
        json.dump(users, f, ensure_ascii= False, indent= 2)

def save_users(users): # ユーザー情報を更新
    with open(USER_FILE, "w", encoding= "utf-8") as f:
        json.dump(users, f, ensure_ascii= False, indent= 2)

def is_admin(user_id):
    return user_id in ADMIN_IDS

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    print(data, flush=True)

    for event in data.get("events", []):

        if event["type"] != "message":
            continue

        message_type = event["message"]["type"] # ローカル関数にしてるのはeventが来た時に使うから
        reply_token = event["replyToken"]
        user_id = event["source"]["userId"]
        users = load_users()
        if message_type == "text":
            text = event["message"]["text"]
        else:
            text = None


        if user_id not in users:
            reply_message(reply_token, "はじめまして。初回利用のため、ユーザー情報を登録します。\n本名を送信してください。")
            add_users(user_id)
            return "OK"

        elif is_admin(user_id) and users[user_id]["admin_status"] != "-":
            admin_status = users[user_id]["admin_status"]
            if admin_status == "None":
                if text == "switch to default mode":
                    reply_message(reply_token, "通常モードに切り替えました。")
                    users[user_id]["admin_status"] = "-"
                    save_users(users)
                    return "OK"
                elif text == "登録":
                    reply_message(reply_token, "登録するプリントの画像を送信してください。")
                    users[user_id]["admin_status"] = "waiting_image"
                    save_users(users)
                    return "OK"
            
            elif admin_status == "waiting_image":
                if event["message"]["type"] == "image":
                    reply_message(reply_token, "プリントの科目名を送信してください。")
                    users[user_id]["admin_status"] = "waiting_subject"
                    save_users(users)
                    return "OK"
                
                elif message_type != "image":
                    reply_message(reply_token, "画像ファイルを送信してください。")
                    return "OK"
                
            elif admin_status == "waiting_subject":
                subject = text
                reply_message(reply_token, "プリント番号を送信してください。")
                users[user_id]["admin_status"] = "waiting_print_number"
                users[user_id]["admin_current_subject"] = subject
                save_users(users)
                return "OK"
            
            elif admin_status == "waiting_print_number":
                print_number = text
                reply_message(reply_token, f"{users[user_id]['admin_current_subject']}のプリント{print_number}を登録しました。")
                users[user_id]["admin_status"] = "None"
                users[user_id]["admin_current_subject"] = "None"
                save_users(users)
                return "OK"

        else:
            register_status = users[user_id]["register_status"]
            service_status = users[user_id]["service_status"]
            subject = users[user_id]["current_subject"]

            if text == "switch to admin mode" and is_admin(user_id):
                reply_message(reply_token, "管理者モードに切り替えました。")
                users[user_id]["admin_status"] = "None"
                save_users(users)
                return "OK"
            
            if register_status == "waiting_name":
                if text == "サービスを利用":
                    reply_message(reply_token, "本名を送信してください。")
                    return "OK"
                else:
                    reply_message(reply_token, "本名を登録しました。次にクラスを送信してください。")
                    users[user_id]["register_status"] = "waiting_class"
                    users[user_id]["name"] = text
                    save_users(users)
                    return "OK"
                
            elif register_status == "waiting_class":
                if text not in ["A", "B", "C", "D"]:
                    reply_message(reply_token, "正しいクラスを送信してください。")
                    return "OK"
                else:
                    reply_message(reply_token, "ユーザー情報の登録が完了しました。")
                    users[user_id]["register_status"] = "registered"
                    users[user_id]["class"] = text
                    save_users(users)
                    return "OK"

            elif register_status == "registered":
                if text == "ユーザー情報再設定":
                    reply_message(reply_token, "ユーザー情報を再設定します。\n本名を送信してください。")
                    users[user_id]["register_status"] = "waiting_name"
                    save_users(users)
                    return "OK"

                if service_status == "None":
                    if text == "サービスを利用":
                        reply_message(reply_token, "科目を選択してください。\n・国語\n・数学\n・英語")
                        users[user_id]["service_status"] = "waiting_subject"
                        save_users(users)
                        return "OK"
                    else:
                        reply_message(reply_token, "こんにちは、" + users[user_id]["name"] + "さん。\n サービスを利用する際は、画面下部の「サービスを利用」ボタンをタップしてください。")
                        return "OK"

                elif service_status == "waiting_subject":
                    if text not in ["国語", "数学", "英語"]:
                        reply_message(reply_token, "利用可能な科目を選択してください。")
                        return "OK"
                    else:
                        reply_message(reply_token, f"{text}が選択されました。\nプリント番号を選択してください。\n・1\n・2\n・3")
                        users[user_id]["service_status"] = "waiting_print_number"
                        users[user_id]["current_subject"] = text
                        save_users(users)
                        return "OK"
                    
                elif service_status == "waiting_print_number":
                    if text not in ["1", "2", "3"]:
                        reply_message(reply_token, "指定されたプリントは見つかりませんでした。正しいプリント番号を選択してください。")
                        return "OK"
                    else:
                        subject = users[user_id]["current_subject"]
                        print_number = text
                        reply_message(reply_token, f"{subject}のプリント{print_number}を送信します。")
                        users[user_id]["service_status"] = "None"
                        users[user_id]["current_subject"] = "None"
                        save_users(users)
                        return "OK"
            else:
                reply_message(reply_token, "エラーが発生しました：登録状態が不明です。")
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