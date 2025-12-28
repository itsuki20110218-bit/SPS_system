from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

BASE_URL = "https://xs738029.xsrv.jp"
PUBLIC_HTML = "/home/xs738029/xs738029.xsrv.jp/public_html"
CHANNEL_ACCESS_TOKEN = "KR7Sclg6pbBPdSFHkwyz3czQpCKOzP6ppszkWFROU8kvM0QdV7XaQ6A7bqDOX27qiZCxBCLA6VWa+Ke85Ekni+Fxwi7vasS9dz4+q5KRVfbIN2uhF2XCSrLaJlsOeQAsnQDUE6O7tFyEZemn72DccAdB04t89/1O/w1cDnyilFU="
USER_FILE = "users.json"
PRINT_FILE = "prints.json"
ADMIN_IDS = [
    "U4eb36bd4d473ed9db5848631fbb6c47d"
    ]

def load_users():
    if not os.path.exists(USER_FILE): 
        return {}
    with open(USER_FILE, "r", encoding= "utf-8") as f: #fとして開く（省略）
        return json.load(f)


def add_users(user_id): # ユーザー情報を追加
    users = load_users()
    users[user_id] = {
        "register_status": "waiting_name",
        "name": "unknown",
        "class": "unknown",
        "service_status": "None",
        "current_subject": "None",
        "mode": "user",
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

def load_prints():
    if not os.path.exists(PRINT_FILE):
        return {}
    with open(PRINT_FILE, "r", encoding= "utf-8") as f:
        return json.load(f)

def save_image(message_id, save_path):
    print_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
        }
    response = requests.get(print_url, headers=headers) #画像データを取得
    with open(save_path, "wb") as f:
        f.write(response.content) #save_pathで指定したファイルを作成して画像データを書き込む

def save_prints(prints):
    with open(PRINT_FILE, "w", encoding= "utf-8") as f:
        json.dump(prints, f, ensure_ascii= False, indent= 2)


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
        prints = load_prints()
        if message_type == "text":
            text = event["message"]["text"]
        else:
            text = None


        if user_id not in users:
            reply_message(reply_token, "はじめまして。初回利用のため、ユーザー情報を登録します。\n本名を送信してください。")
            add_users(user_id)
            return "OK"

        elif users[user_id]["mode"] == "admin":
            admin_status = users[user_id]["admin_status"]
            if admin_status == "ready":
                if text == "switch to default mode":
                    reply_message(reply_token, "通常モードに切り替えました。")
                    users[user_id]["admin_status"] = "idle"
                    users[user_id]["mode"] = "user"
                    save_users(users)
                    return "OK"

                elif text == "登録":
                    reply_message(reply_token, "登録するプリントの画像を送信してください。")
                    users[user_id]["admin_status"] = "waiting_image"
                    save_users(users)
                    return "OK"
            
            elif admin_status == "waiting_image":
                if message_type == "image":
                    reply_message(reply_token, "プリントの科目名を送信してください。")
                    message_id = event["message"]["id"]
                    os.makedirs("temp", exist_ok=True) #tempフォルダ（一時保存用）を作成
                    temp_path = f"temp/{message_id}.jpg" #パス作成
                    save_image(message_id, temp_path)
                    users[user_id]["admin_status"] = "waiting_subject"
                    users[user_id]["admin_temp_image"] = temp_path
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
                subject = users[user_id]["admin_current_subject"]
                temp_path = users[user_id]["admin_temp_image"]

                prints_dir = os.path.join(PUBLIC_HTML, "prints")
                os.makedirs(prints_dir, exist_ok=True)
                save_path = os.path.join(
                    prints_dir,
                    f"{subject}_{print_number}.jpg"
                )

                os.rename(temp_path, save_path) #ファイルをsave_pathで指定した場所に移動

                prints = load_prints()
                prints.setdefault(subject, {})[print_number] = f"prints/{subject}_{print_number}.jpg"
                save_prints(prints)

                users[user_id]["admin_status"] = "ready"
                users[user_id]["admin_current_subject"] = "None"
                users[user_id].pop("admin_temp_image", None)
                save_users(users)

                reply_message(reply_token, f"{subject}のプリント{print_number}を登録しました。")
                return "OK"

        else:
            register_status = users[user_id]["register_status"]
            service_status = users[user_id]["service_status"]
            subject = users[user_id]["current_subject"]

            if text == "switch to admin mode" and is_admin(user_id): # 管理モードに切り替え
                reply_message(reply_token, "管理モードに切り替えました。")
                users[user_id]["admin_status"] = "ready"
                users[user_id]["mode"] = "admin"
                save_users(users)
                return "OK"
            
            elif register_status == "waiting_name":
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
                    if is_admin(user_id):
                        users[user_id]["mode"] = "admin"
                        users[user_id]["admin_status"] = "ready"

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
                    subject = text.strip()
                    if subject not in prints:
                        reply_message(reply_token, "利用可能な科目を選択してください。")
                        return "OK"
                    else:
                        reply_message(reply_token, f"{subject}が選択されました。\nプリント番号を選択してください。")
                        users[user_id]["service_status"] = "waiting_print_number"
                        users[user_id]["current_subject"] = subject
                        save_users(users)
                        return "OK"
                    
                elif service_status == "waiting_print_number":
                        subject = users[user_id]["current_subject"]
                        print_number = text

                        if not print_number.isdigit():
                            reply_message(reply_token, "プリント番号は数字で送信してください。")
                            return "OK"
                        
                        else:
                            if print_number not in prints[subject]:
                                reply_message(reply_token, "指定されたプリントは見つかりませんでした。")
                                return "OK"
                            
                            else:
                                image_path = prints[subject][print_number]
                                image_url = f"{BASE_URL}/{image_path}"

                                reply_image(reply_token, image_url)
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

def reply_image(reply_token, image_url):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
        }
    body = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url
            }
        ]
    }
    requests.post(url, headers=headers, data=json.dumps(body))
    