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
ADMIN_IDS = "admin_ids.json"

classes = ["A", "B", "C", "D"]
all_subjects = ["国語", "数学", "理科", "公民", "英語"]
        
def load_admin_ids():
    if not os.path.exists(ADMIN_IDS):
        return "OK"
    with open(ADMIN_IDS, "r", encoding="utf-8") as f:
        return json.load(f)
    
def load_users():
    if not os.path.exists(USER_FILE): 
        return []
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
        "violation": 0
    }
    with open(USER_FILE, "w", encoding= "utf-8") as f:
        json.dump(users, f, ensure_ascii= False, indent= 2)

def save_users(users): # ユーザー情報を更新
    with open(USER_FILE, "w", encoding= "utf-8") as f:
        json.dump(users, f, ensure_ascii= False, indent= 2)

def is_admin(user_id):
    return user_id in load_admin_ids()

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
            return "OK"

        message_type = event["message"]["type"] #ローカル関数にしてるのはeventが来た時に使うから
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
                users[user_id].pop("current_print_number", None)
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
                
                elif text == "カテゴリ作成":
                    users[user_id]["admin_status"] = "waiting_category_subject"
                    save_users(users)
                    reply_message(reply_token, "科目を選択してください。", show_cancel=True, show_subjects=True)
                    return "OK"
                
                elif text == "その他":
                    reply_message(reply_token, "削除する教材の科目を選択してください。", show_cancel=True, show_subjects=True)
                    users[user_id]["admin_status"] = "waiting_delete_subject"
                    save_users(users)
                    return "OK"
                
                elif text == "編集":
                    reply_message(reply_token, "編集する教材の科目を選択してください。", show_cancel=True, show_subjects=True)
                    users[user_id]["admin_status"] = "waiting_edit_subject"
                    save_users(users)
                    return "OK"
                
                else:
                    return "OK"
            
            elif admin_status == "waiting_delete_subject":
                subject = text.strip()
                if subject not in prints:
                    reply_message(reply_token, "指定された科目は存在しません。", show_cancel=True, show_subjects=True)
                    save_users(users)
                    return "OK"
                else:
                    users[user_id]["admin_status"] = "waiting_delete_print_category"
                    users[user_id]["admin_current_subject"] = subject
                    users[user_id]["print_page"] = 0
                    save_users(users)
                    reply_message(reply_token, "カテゴリを選択してください。", show_cancel=True, show_categories=True, user_id=user_id)
                    return "OK"
                
            elif admin_status == "waiting_delete_print_category":
                category = text.strip()
                subject = users[user_id]["admin_current_subject"]
                if category not in prints.get(subject, {}):
                    reply_message(reply_token, "存在しないカテゴリ名です。", show_cancel=True, show_categories=True, user_id=user_id)
                    return "OK"
                
                users[user_id]["admin_current_category"] = category
                users[user_id]["admin_status"] = "waiting_delete_print_number"
                save_users(users)
                reply_message(reply_token, "削除する教材を選択してください。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                return "OK"

            elif admin_status == "waiting_delete_print_number":
                print_number = text.strip()
                subject = users[user_id]["admin_current_subject"]
                category = users[user_id]["admin_current_category"]
                if text == "次へ":
                        all_numbers = list(prints[subject][category].keys())
                        max_page = (len(all_numbers) - 1) // 11

                        if max_page <= users[user_id]["print_page"]:
                            return "OK"

                        else:
                            users[user_id]["print_page"] += 1
                            save_users(users)
                            reply_message(reply_token, "次を表示します。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                            return "OK"
                        
                if print_number not in prints[subject][category]:
                    reply_message(reply_token, "指定された教材は存在しません。")
                    users[user_id]["admin_status"] = "ready"
                    users[user_id].pop("admin_current_subject", None)
                    users[user_id].pop("print_page",  None)
                    save_users(users)
                    return "OK"

                image_path = prints[subject][category][print_number]
                file_path = os.path.join(PUBLIC_HTML, image_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
                del prints[subject][category][print_number]

                if not prints[subject][category]:
                    category_dir = os.path.join(PUBLIC_HTML, "prints", subject, category)
                    os.rmdir(category_dir)
                    del prints[subject][category]

                if not prints[subject]:
                    subject_dir = os.path.join(PUBLIC_HTML, "prints", subject)
                    os.rmdir(subject_dir)
                    del prints[subject]

                save_prints(prints)
                users[user_id].pop("print_page", None)
                users[user_id]["admin_status"] = "ready"
                users[user_id].pop("admin_current_subject", None)
                users[user_id].pop("admin_current_category", None)
                save_users(users)
                reply_message(reply_token, f"削除済み：{subject} - {print_number}")
                return "OK"
            
            elif admin_status == "waiting_edit_subject":
                subject = text.strip()
                if subject not in prints:
                    reply_message(reply_token, "指定された科目は存在しません。")
                    users[user_id]["admin_status"] = "ready"
                    save_users(users)
                    return "OK"
                
                else:
                    users[user_id]["admin_status"] = "waiting_edit_print"
                    users[user_id]["admin_current_subject"] = subject
                    users[user_id]["print_page"] = 0
                    save_users(users)
                    reply_message(reply_token, "教材を選択してください。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                    return "OK"

            elif admin_status == "waiting_edit_print":
                subject = users[user_id]["admin_current_subject"]
                print_number = text.strip()
                if text == "次へ":
                    all_numbers = list(prints[subject].keys())
                    max_page = (len(all_numbers) - 1)// 11
                    if max_page <= users[user_id]["print_page"]:
                        return "OK"
                    
                    else:
                        users[user_id]["print_page"] += 1
                        save_users(users)
                        reply_message(reply_token, "次を表示します。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                        return "OK"
                
                elif print_number not in prints[subject]:
                    reply_message(reply_token, "指定された教材は存在しません。")
                    users[user_id]["admin_status"] = "ready"
                    users[user_id].pop("admin_current_subject", None)
                    users[user_id].pop("print_page", None)
                    save_users(users)
                    return "OK"
                
                    
                else:
                    reply_message(reply_token, "指定した教材の新しい名称を送信して下さい。", show_cancel=True)
                    users[user_id]["admin_status"] = "waiting_new_print_number"
                    users[user_id]["current_print_number"] = print_number
                    users[user_id].pop("print_page", None)
                    save_users(users)
                    return "OK"

            elif admin_status == "waiting_new_print_number":
                new_print_number = text.strip()
                subject = users[user_id]["admin_current_subject"]
                old_print_number = users[user_id]["current_print_number"]
                if new_print_number in prints[subject]:
                    reply_message(reply_token, "すでに存在する名称です。新しい名称を送信してください。", show_cancel=True)
                    return "OK"
                
                else:
                    old_path = prints[subject][old_print_number]
                    old_full_path = os.path.join(PUBLIC_HTML, old_path)
                    new_path = f"prints/{subject}/{new_print_number}.jpg"
                    new_full_path = os.path.join(PUBLIC_HTML, new_path)
                    os.rename(old_full_path, new_full_path)

                    prints[subject][new_print_number] = new_path
                    del prints[subject][old_print_number]
                    save_prints(prints)

                    users[user_id]["admin_status"] = "ready"
                    users[user_id].pop("admin_current_subject", None)
                    users[user_id].pop("current_print_number", None)
                    save_users(users)

                    reply_message(reply_token, f"{new_print_number}に変更しました。")
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
                subject = text.strip()
                if subject not in all_subjects:
                    reply_message(reply_token, "不明な科目です。\n一覧から科目を選択してください。", show_cancel=True, show_subjects=True)
                    return "OK"
                
                users[user_id]["admin_status"] = "waiting_category"
                users[user_id]["admin_current_subject"] = subject
                save_users(users)
                reply_message(reply_token, "カテゴリを選択してください。", show_cancel=True, show_categories=True, user_id=user_id)
                return "OK"
            
            elif admin_status == "waiting_category":
                category = text.strip()
                subject = users[user_id]["admin_current_subject"]
                if category not in prints.get(subject, {}):
                    reply_message(reply_token, "存在しないカテゴリ名です。", show_cancel=True, show_categories=True, user_id=user_id)
                    return "OK"
                
                users[user_id]["admin_current_category"] = category
                users[user_id]["admin_status"] = "waiting_print_number"
                save_users(users)
                reply_message(reply_token, "教材の名称を送信してください。")
                return "OK"
            
            elif admin_status == "waiting_print_number":
                print_number = text.strip()
                subject = users[user_id]["admin_current_subject"]
                category = users[user_id]["admin_current_category"]
                temp_path = users[user_id]["admin_temp_image"]

                if print_number in prints.get(subject, {}).get(category, {}):
                    reply_message(reply_token, "すでに存在する名称です。新しい名称を送信してください。", show_cancel=True)
                    return "OK"
                
                else:
                    prints_dir = os.path.join(PUBLIC_HTML, "prints", subject, category)
                    os.makedirs(prints_dir, exist_ok=True)
                    save_path = os.path.join(prints_dir, f"{print_number}.jpg")

                    os.rename(temp_path, save_path) #ファイルをsave_pathで指定した場所に移動

                    prints.setdefault(subject, {}).setdefault(category, {})[print_number] = f"prints/{subject}/{category}/{print_number}.jpg"
                    save_prints(prints)

                    users[user_id]["admin_status"] = "ready"
                    users[user_id].pop("admin_current_subject", None)
                    users[user_id].pop("admin_current_category", None)
                    users[user_id].pop("admin_temp_image", None)
                    save_users(users)

                    reply_message(reply_token, f"{subject} - {category} - {print_number}が正常に登録されました。")
                    return "OK"
                
            elif admin_status == "waiting_category_subject":
                subject = text.strip()
                if subject not in all_subjects:
                    reply_message(reply_token, "不明な科目です。\n一覧から科目を選択してください。", show_cancel=True, show_subjects=True)
                    return "OK"
                
                prints.setdefault(subject, {})
                save_prints(prints)
                users[user_id]["admin_status"] = "waiting_category_name"
                users[user_id]["admin_current_subject"] = subject
                save_users(users)
                reply_message(reply_token, "カテゴリ名を送信してください。", show_cancel=True)
                return "OK"
            
            elif admin_status == "waiting_category_name":
                category_name = text.strip()
                subject = users[user_id].get("admin_current_subject")
                if category_name in prints[subject]:
                    reply_message(reply_token, "すでに存在するカテゴリ名です。", show_cancel=True)
                    return "OK"
                
                category_dir = os.path.join(PUBLIC_HTML, "prints", subject, category_name)
                os.makedirs(category_dir, exist_ok=True)
                prints[subject][category_name] = {}
                save_prints(prints)

                users[user_id].pop("admin_current_subject", None)
                users[user_id]["admin_status"] = "ready"
                save_users(users)
                reply_message(reply_token, f"{subject}内に{category_name}が正常に作成されました。")
                return "OK"

        else:
            register_status = users[user_id]["register_status"]
            service_status = users[user_id]["service_status"]
            subject = users[user_id]["current_subject"]

            if text == "モード切り替え" and is_admin(user_id): #管理モードに切り替え
                reply_message(reply_token, "管理モードに切り替えました。")
                users[user_id]["admin_status"] = "ready"
                users[user_id]["mode"] = "admin"
                save_users(users)
                return "OK"
            
            if users[user_id]["violation"] == 5:
                reply_message(reply_token, f"警告：無効な操作の合計回数が{users[user_id]['violation']}に達しました。\nプログラムの故障に繋がる可能性がありますので、これらの行為はお控えください。\n繰り返した場合には、ユーザー登録を再度行っていただきますのでご了承ください。")
                users[user_id]["violation"] += 1
                save_users(users)
                return "OK"
            
            if users[user_id]["violation"] >= 10:
                reply_message(reply_token, "申し訳ありませんが、現在、あなたはSPSを利用できない状態です。")
                return "OK"

            elif register_status == "waiting_name":
                if text in ["もらう", "その他"] or len(text) > 6 or len(text) <= 2 or text == None:
                    reply_message(reply_token, f'"{text}"は登録できません。\n本名の送信をお願いします。')
                    users[user_id]["violation"] += 1
                    save_users(users)
                    return "OK"
                
                else:
                    name = text.strip()
                    reply_message(reply_token, f"{name}さんでよろしいですか？", show_confirm=True)
                    users[user_id]["register_status"] = "waiting_comfirm" #service_statusではない
                    users[user_id]["name"] = name
                    save_users(users)
                    return "OK"
                
            elif register_status == "waiting_comfirm":
                if text == "はい":
                    name = users[user_id]["name"]
                    reply_message(reply_token, f"ありがとうございます。\n次に{name}さんのクラスを選択してください。", show_class=True)
                    users[user_id]["register_status"] = "waiting_class"
                    save_users(users)
                    return "OK"
                
                elif text == "いいえ":
                    reply_message(reply_token, "本名の送信をお願いします。")
                    users[user_id]["register_status"] = "waiting_name"
                    users[user_id]["name"] = "unknown"
                    save_users(users)
                    return "OK"
                
                else:
                    reply_message(reply_token, "無効な操作です。\nトーク画面の最下部までスワイプし、「はい」または「いいえ」の選択をお願いします。", show_confirm=True)
                    users[user_id]["violation"] += 1
                    save_users(users)
                    return "OK"
                
            elif register_status == "waiting_class":
                if text not in classes:
                    reply_message(reply_token, "指定されたクラスは見つかりませんでした。\nトーク画面の最下部までスワイプし、一覧からの選択をお願いします。", show_class=True)
                    users[user_id]["violation"] += 1
                    save_users(users)
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
                if text == None:
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
                        reply_message(reply_token, "ご希望の操作を一覧から選択してください。", show_others=True)
                        return "OK"
                    
                    elif text == "ユーザー情報の再設定":
                        reply_message(reply_token, "ユーザー情報を再設定します。\n本名を送信してください。")
                        users[user_id]["register_status"] = "waiting_name"
                        save_users(users)
                        return "OK"
                    
                    elif text == "お問い合わせ":
                        reply_message(reply_token, "お問い合わせは、担当者による手動の対応となります。\nよろしいですか？", show_confirm=True)
                        users[user_id]["service_status"] = "waiting_confirm"
                        save_users(users)
                        return "OK"
                    
                    else:
                        reply_message(reply_token, f"こんにちは、{name}さん。\nSPSを利用するには、下部のメニューから「もらう」をタップしてください。")
                        return "OK"
                        

                elif service_status == "waiting_subject":
                    subject = text.strip()
                    if subject in all_subjects:
                        if subject not in prints:
                            reply_message(reply_token, f"{subject}は手動での対応となります。\nよろしいですか？", show_confirm=True)
                            users[user_id]["service_status"] = "waiting_confirm"
                            save_users(users)
                            return "OK"
                        
                        else:
                            users[user_id]["service_status"] = "waiting_print_number"
                            users[user_id]["current_subject"] = subject
                            users[user_id]["print_page"] = 0
                            save_users(users)
                            reply_message(reply_token, f"ご希望の教材を一覧から選択してください。\n一覧にない場合は手動対応となりますので、教材名の送信をお願いします。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                            return "OK"
                        
                    else:
                        reply_message(reply_token, f"指定された科目は見つかりませんでした。\nトーク画面の最下部までスワイプし、科目一覧からの選択をお願いします。", show_cancel=True, show_subjects=True)
                        users[user_id]["violation"] += 1
                        save_users(users)
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
                                reply_message(reply_token, f"（{users[user_id]['print_page'] +1}/{max_page +1} ）\n一覧にない場合は手動対応となりますので、教材名の送信をお願いします。", show_cancel=True, show_print_numbers=True, user_id=user_id)
                                return "OK"


                        print_number = text.strip()

                        if print_number not in prints[subject]:
                            reply_message(reply_token, f'"{print_number}"は、担当者による手動での対応となります。\nよろしいですか？', show_confirm=True, show_cancel=True)
                            users[user_id]["service_status"] = "waiting_confirm"
                            users[user_id].pop("print_page", None)
                            save_users(users)
                            return "OK"
                        
                            
                        else:
                            image_path = quote(prints[subject][print_number])
                            image_url = f"{BASE_URL}/{image_path}"

                            reply_image(reply_token, image_url, subject, print_number)
                            users[user_id]["service_status"] = "done"
                            users[user_id].pop("print_page", None)
                            save_users(users)
                            return "OK"
                        
                elif service_status == "waiting_confirm":
                    if text == "はい":
                        reply_message(reply_token, "担当者におつなぎします。\n返信までしばらくお待ちください。", show_cancel=True)
                        users[user_id]["service_status"] = "done"
                        users[user_id]["current_subject"] = "None"
                        save_users(users)
                        return "OK"

                    elif text == "いいえ":
                        reply_message(reply_token, "キャンセルしました。")
                        users[user_id]["service_status"] = "None"
                        users[user_id]["current_subject"] = "None"
                        save_users(users)
                        return "OK"
                    
                    else:
                        reply_message(reply_token, "無効な操作です。\nトーク画面の最下部までスワイプし、「はい」または「いいえ」の選択をお願いします。", show_confirm=True)
                        users[user_id]["violation"] += 1
                        save_users(users)
                        return "OK"
                        
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
                        users[user_id]["print_page"] = 0
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
                        users[user_id]["current_subject"] = "None"
                        users[user_id]["service_status"] = "waiting_subject"
                        save_users(users)
                        return "OK"
                    
                    elif text == "その他":
                        reply_message(reply_token, "操作を一覧から選択してください。", show_others=True)
                        users[user_id]["service_status"] = "None"
                        users[user_id]["current_subject"] = "None"
                        save_users(users)
                        return "OK"
                    
                    else:
                        users[user_id]["service_status"] = "None"
                        users[user_id]["current_subject"] = "None"
                        save_users(users)
                        return "OK"

                            
            else:
                reply_message(reply_token, "エラーが発生しました：登録状態が不明です。")
                return "OK"

def reply_message(reply_token, text, show_cancel=False, show_class=False, show_print_numbers=False, show_subjects=False, show_end=False, show_categories=False, show_confirm=False, show_others=False, user_id=None):
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
        items = [
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": "はい",
                    "text": "はい"
                }
            },
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": "いいえ",
                    "text": "いいえ"
                }
            }
        ]

    if show_others:
        items = [
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": "ユーザー情報の再設定",
                    "text": "ユーザー情報の再設定"
                }
            },
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": "お問い合わせ",
                    "text": "お問い合わせ"
                }
            }
        ]
    users= load_users()
    prints = load_prints()

    if show_categories:
        subject = (
        users[user_id].get("admin_current_subject")
        if users[user_id]["mode"] == "admin"
        else users[user_id].get("current_subject")
        )
        all_categories = list(prints.get(subject, {}).keys())
        for category in all_categories:
            items.append({
                "type": "action",
                "action": {
                    "type": "message",
                    "label": category,
                    "text": category
                }
            })

    if show_print_numbers:
        subject = (
        users[user_id].get("admin_current_subject")
        if users[user_id]["mode"] == "admin"
        else users[user_id].get("current_subject")
        )
        category = users[user_id].get("admin_current_category") #あとで修正

        page = users[user_id].get("print_page", 0)
        all_numbers = list(prints[subject][category].keys())
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
                                "label": f"続けて{subject}の教材をもらう",
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
