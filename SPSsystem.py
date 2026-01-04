from flask import Flask, request
import requests
import json
import os
from urllib.parse import quote

app = Flask(__name__)

BASE_URL = "https://xs738029.xsrv.jp"
PUBLIC_HTML = "/home/xs738029/xs738029.xsrv.jp/public_html"
CHANNEL_ACCESS_TOKEN = "KR7Sclg6pbBPdSFHkwyz3czQpCKOzP6ppszkWFROU8kvM0QdV7XaQ6A7bqDOX27qiZCxBCLA6VWa+Ke85Ekni+Fxwi7vasS9dz4+q5KRVfbIN2uhF2XCSrLaJlsOeQAsnQDUE6O7tFyEZemn72DccAdB04t89/1O/w1cDnyilFU="
USER_FILE = "users.json"
PRINT_FILE = "prints.json"
ADMIN_IDS = [
    "U4eb36bd4d473ed9db5848631fbb6c47d",
    "Ue7081ca5b49a297b2bf0c359726da764"
    ]

classes = ["A", "B", "C", "D"]
all_subjects = ["国語", "数学", "理科", "公民", "英語"]

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
        "admin_status": "-"
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

def get_print_numbers_by_page(numbers, page, per_page=11):
    start = page * per_page
    end = start + per_page
    return numbers[start:end]


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

            if text == "キャンセル" and admin_status != "ready":
                users[user_id]["admin_status"] = "ready"
                users[user_id].pop("admin_current_subject", None)
                users[user_id].pop("admin_temp_image", None)
                users[user_id].pop("print_page", None)
                save_users(users)
                reply_message(reply_token, "キャンセルしました。")
                return "OK"

            if admin_status == "ready":
                if text == "モード切り替え":
                    reply_message(reply_token, "通常モードに切り替えました。")
                    users[user_id]["admin_status"] = "idle"
                    users[user_id]["mode"] = "user"
                    save_users(users)
                    return "OK"
            
                elif text == "もらう":
                    reply_message(reply_token, "登録する教材の画像を送信してください。", show_cancel=True)
                    users[user_id]["admin_status"] = "waiting_image"
                    save_users(users)
                    return "OK"
                
                elif text == "その他":
                    reply_message(reply_token, "削除する教材の教科を選択してください。", show_cancel=True, show_subjects=True)
                    users[user_id]["admin_status"] = "waiting_delete_subject"
                    save_users(users)
                    return "OK"
            
            elif admin_status == "waiting_delete_subject":
                subject = text.strip()
                if subject not in prints:
                    reply_message(reply_token, "指定された教科は存在しません。")
                    users[user_id]["admin_status"] = "ready"
                    save_users(users)
                    return "OK"
                else:
                    users[user_id]["admin_status"] = "waiting_delete_print"
                    users[user_id]["admin_current_subject"] = subject
                    users[user_id]["print_page"] = 0
                    save_users(users)
                    reply_message(reply_token, "教材を選択してください。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                    return "OK"

            elif admin_status == "waiting_delete_print":
                subject = users[user_id]["admin_current_subject"]
                print_number = text.strip()
                if text == "次へ":
                        all_numbers = list(prints[subject].keys())
                        max_page = (len(all_numbers) - 1) // 11

                        if max_page <= users[user_id]["print_page"]:
                            return "OK"

                        else:
                            users[user_id]["print_page"] += 1
                            save_users(users)
                            reply_message(reply_token, "次を表示します。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                            return "OK"
                        
                if print_number not in prints[subject]:
                    reply_message(reply_token, "指定された教材は存在しません。")
                    users[user_id]["admin_status"] = "ready"
                    users[user_id].pop("admin_current_subject", None)
                    users[user_id].pop("print_page",  None)
                    save_users(users)
                    return "OK"

                else:
                    image_path = prints[subject][print_number]
                    file_path = os.path.join(PUBLIC_HTML, image_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    del prints[subject][print_number]

                    if not prints[subject]:
                        del prints[subject]

                    reply_message(reply_token, f"削除済み：{subject} - {print_number}")
                    users[user_id].pop("print_page", None)
                    save_prints(prints)

                users[user_id]["admin_status"] = "ready"
                users[user_id].pop("admin_current_subject", None)
                save_users(users)
                return "OK"


            elif admin_status == "waiting_image":
                if message_type == "image":
                    reply_message(reply_token, "科目を選択してください。", show_cancel=True, show_subjects=True)
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
                if subject not in all_subjects:
                    reply_message(reply_token, "不明な科目です。\n一覧から科目を選択してください。", show_cancel=True, show_subjects=True)
                    return "OK"
                reply_message(reply_token, "教材名を送信してください。", show_cancel=True)
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
                users[user_id].pop("admin_current_subject", None)
                users[user_id].pop("admin_temp_image", None)
                save_users(users)

                reply_message(reply_token, f"{subject} - {print_number}が正常に登録されました。")
                return "OK"

        else:
            register_status = users[user_id]["register_status"]
            service_status = users[user_id]["service_status"]
            subject = users[user_id]["current_subject"]

            if text == "モード切り替え" and is_admin(user_id): # 管理モードに切り替え
                reply_message(reply_token, "管理モードに切り替えました。")
                users[user_id]["admin_status"] = "ready"
                users[user_id]["mode"] = "admin"
                save_users(users)
                return "OK"
            
            elif register_status == "waiting_name":
                if text in ["もらう", "その他"] or len(text) > 6 or len(text) <= 2:
                    reply_message(reply_token, f'"{text}"は登録できません。\n本名の送信をお願いします。')
                    return "OK"
                
                else:
                    name = text.strip()
                    reply_message(reply_token, f"ありがとうございます。\n次に{name}さんのクラスを選択してください。", show_class=True)
                    users[user_id]["register_status"] = "waiting_class"
                    users[user_id]["name"] = name
                    save_users(users)
                    return "OK"
                
            elif register_status == "waiting_class":
                if text not in classes:
                    reply_message(reply_token, "正しいクラスを送信してください。")
                    return "OK"
                else:
                    reply_message(reply_token, "ご協力ありがとうございました。以上で初期設定は完了です。\nSPSを利用するには、下部のメニューから「もらう」をタップしてください。")
                    users[user_id]["register_status"] = "registered"
                    users[user_id]["class"] = text
                    if is_admin(user_id):
                        users[user_id]["mode"] = "admin"
                        users[user_id]["admin_status"] = "ready"

                    save_users(users)
                    return "OK"

            elif register_status == "registered":
                if text == "ユーザー情報を再設定":
                    reply_message(reply_token, "ユーザー情報を再設定します。\n本名を送信してください。")
                    users[user_id]["register_status"] = "waiting_name"
                    save_users(users)
                    return "OK"

                elif text == "キャンセル" and service_status != "None":
                    reply_message(reply_token, "キャンセルしました。")
                    users[user_id]["service_status"] = "None"
                    users[user_id]["current_subject"] = "None"
                    users[user_id].pop("print_page", None)
                    save_users(users)
                    return "OK"
                
                elif service_status == "None":
                    name = users[user_id]["name"]
                    if text == "もらう":
                        reply_message(reply_token, f"こんにちは、{name}さん。\nご希望の科目を選択してください。", show_cancel=True, show_subjects=True)
                        users[user_id]["service_status"] = "waiting_subject"
                        save_users(users)
                        return "OK"
                    
                    elif text == "その他":
                        reply_message(reply_token, "メッセージありがとうございます。\nこの機能は現在開発中です。\n申し訳ありませんが、正式なリリースまでもうしばらくお待ちください。")
                        return "OK"
                    
                    else:
                        reply_message(reply_token, f"こんにちは、{name}さん。\nSPSを利用するには、下部のメニューから「もらう」をタップしてください。")
                        return "OK"
                        

                elif service_status == "waiting_subject":
                    subject = text.strip()
                    if subject in all_subjects:
                        if subject not in prints:
                            reply_message(reply_token, f"{subject}は手動での対応となります。\n担当者へお繋ぎしますか？", show_confirm=True, show_cancel=True)
                            users[user_id]["service_status"] = "waiting_confirm"
                            save_users(users)
                            return "OK"
                        else:
                            users[user_id]["service_status"] = "waiting_print_number"
                            users[user_id]["current_subject"] = subject
                            users[user_id]["print_page"] = 0
                            save_users(users)
                            reply_message(reply_token, f"ご希望の教材を一覧から選択してください。\n一覧にない場合は、教材名をチャットで送信してください。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                            return "OK"
                        
                    else:
                        reply_message(reply_token, f"指定された科目は見つかりませんでした。\n下部の一覧から選択してください。", show_cancel=True, show_subjects=True)
                        return "OK"
                
                elif service_status == "waiting_print_number":
                        subject = users[user_id]["current_subject"]

                        if text == "次へ":
                            all_numbers = list(prints[subject].keys())
                            max_page = (len(all_numbers) - 1) // 11

                            if max_page <= users[user_id]["print_page"]:
                                return "OK"

                            else:
                                users[user_id]["print_page"] += 1
                                save_users(users)
                                reply_message(reply_token, "次を表示します。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                                return "OK"


                        print_number = text.strip()

                        if print_number not in prints[subject]:
                            reply_message(reply_token, f"{print_number}は手動での対応となります。\n担当者へおつなぎしますか？", show_confirm=True, show_cancel=True)
                            users[user_id]["service_status"] = "waiting_confirm"
                            save_users(users)
                            return "OK"
                        
                            
                        else:
                            image_path = prints[subject][print_number]
                            encoded_path = quote(image_path)
                            image_url = f"{BASE_URL}/{encoded_path}"

                            reply_image(reply_token, image_url, subject, print_number)
                            users[user_id]["service_status"] = "done"
                            users[user_id].pop("print_page", None)
                            save_users(users)
                            return "OK"
                        
                elif service_status == "waiting_confirm":
                    if text == "続ける":
                        reply_message(reply_token, "担当者におつなぎします。\n返信までしばらくお待ちください。", show_cancel=True)
                        users[user_id]["service_status"] = "done"
                        users[user_id]["current_subject"] = "None"
                        save_users(users)
                        return "OK"

                    elif text == "キャンセル":
                        reply_message(reply_token, "キャンセルしました。")
                        users[user_id]["service_status"] = "None"
                        users[user_id]["current_subject"] = "None"
                        save_users(users)
                        return "OK"
                    
                    else:
                        reply_message(reply_token, "", show_confirm=True, show_cancel=True)
                        
                elif service_status == "done":
                    if text == "終了する":
                        reply_message(reply_token, "ご利用ありがとうございました。")
                        users[user_id]["service_status"] = "None"
                        users[user_id]["current_subject"] = "None"
                        save_users(users)
                        return "OK"

                    elif text == "続ける":
                        subject = users[user_id]["current_subject"]
                        reply_message(reply_token, "ご希望の教材を一覧から選択してください。\n一覧にない場合は、教材名をチャットで送信してください。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                        users[user_id]["service_status"] = "waiting_print_number"
                        users[user_id]["page"] = 0
                        save_users(users)
                        return "OK"
                    
                    elif text =="キャンセル":
                        reply_message(reply_token, "キャンセルしました。")
                        users[user_id]["service_status"] = "None"
                        users[user_id]["current_subject"] = "None"
                        save_users(users)
                        return "OK"
                    
                    elif text == "もらう":
                        name = users[user_id]["name"]
                        reply_message(reply_token, f"こんにちは、{name}さん。\nご希望の科目を選択してください。", show_cancel=True, show_subjects=True)
                        users[user_id]["service_status"] = "waiting_subject"
                        save_users(users)
                        return "OK"
                    
                    else:
                        users[user_id]["service_status"] = "None"
                        users[user_id]["current_subject"] = "None"
                        return "OK"

                            
            else:
                reply_message(reply_token, "エラーが発生しました：登録状態が不明です。")
                return "OK"

def reply_message(reply_token, text, show_cancel=False, show_class=False, show_print_numbers=False, show_subjects=False, show_end=False, show_confirm=False, user_id = None):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    message = {
            "type": "text",
            "text": text
        }
        
    items = []
    if show_class:
        for i in classes:
            items.append({
                "type": "action",
                "action": {
                    "type": "message",
                    "label": i,
                    "text": i
                }
            })
        
    if show_end:
        items.append({
            "type": "action",
            "action": {
                "type": "message",
                "label": "終了する",
                "text": "終了する"
                }
            }
        )

    if show_subjects:
        for subject in all_subjects:
            items.append({
                "type": "action",
                "action": {
                    "type": "message",
                    "label": subject,
                    "text": subject
                }
            })

    if show_confirm:
        items.append({
            "type": "action",
            "action": {
                "type": "message",
                "label": "続ける",
                "text": "続ける"
            }
        })

    if show_print_numbers:
        prints = load_prints()
        users = load_users()
        if users[user_id]["mode"] == "admin":
            subjects = users[user_id]["admin_current_subject"]
        else:
            subjects = users[user_id]["current_subject"]
            
        page = users[user_id].get("print_page", 0)

        all_numbers = list(prints.get(subjects, {}).keys())
        page_numbers = get_print_numbers_by_page(all_numbers, page)

        for number in page_numbers:
            items.append({
                "type": "action",
                "action": {
                    "type": "message",
                    "label": number,
                    "text": number
                }
            })

        if (page + 1) * 11 < len(all_numbers):
            items.append({
                "type": "action",
                "action": {
                    "type": "message",
                    "label": "次へ",
                    "text": "次へ"
                }
            })
            
        
    if show_cancel:
        items.append({
            "type": "action",
            "action": {
                "type": "message",
                "label": "キャンセル",
                "text": "キャンセル"
            }
    })

    if items:
        message["quickReply"] = {
            "items": items
        }

    
    body = {
        "replyToken": reply_token,
        "messages": [message]
    }
    requests.post(url, headers=headers, data=json.dumps(body))

def reply_image(reply_token, image_url, subject, print_number):
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
            },
            {
                "type": "text",
                "text": f"{subject}の{print_number}です。",
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": f"{subject}の取得を続ける",
                                "text": "続ける"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": "終了する",
                                "text": "終了する"
                            }
                        }
                    ]
                }
            }
        ]
    }

    requests.post(url, headers=headers, data=json.dumps(body))