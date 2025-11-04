import os

import requests
import gspread

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        """Fallback when python-dotenv is not installed."""
        print("[警告] python-dotenvが未インストールのため、.env読み込みをスキップします")
        return False
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# 🔍 トークンの確認ログ
if ACCESS_TOKEN:
    print("トークンチェック（ACCESS_TOKENの先頭10文字）:", ACCESS_TOKEN[:10] + "***")
else:
    print("[警告] ACCESS_TOKENが未設定です")

# Google Sheets接続
def get_sheet():
    if not SPREADSHEET_URL:
        print("[警告] SPREADSHEET_URLが未設定のため、シートの読み込みをスキップします")
        return None

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SPREADSHEET_URL).sheet1
        return sheet
    except Exception as e:
        print("[警告] シートの取得に失敗しました:", e)
        return None

# 広告の現在ステータスを確認
def fetch_ad_status(ad_id):
    if not ACCESS_TOKEN:
        print("[警告] ACCESS_TOKENが未設定のため、広告ステータスの取得をスキップします")
        return {}

    url = f"https://graph.facebook.com/v19.0/{ad_id}?fields=status,effective_status&access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    print(f"広告ステータス確認: {res.text}")
    return res.json()

# Meta広告を停止する
def pause_ad(ad_id):
    ad_status = fetch_ad_status(ad_id)
    effective_status = ad_status.get("effective_status") or ad_status.get("status")

    if effective_status in ["PAUSED", "ARCHIVED"]:
        print(f"スキップ: {ad_id} はすでに停止済み（ステータス: {effective_status}）")
        return False

    if not ACCESS_TOKEN:
        print("[警告] ACCESS_TOKENが未設定のため、広告の停止をスキップします")
        return False

    url = f"https://graph.facebook.com/v19.0/{ad_id}"
    data = {
        "status": "PAUSED",
        "access_token": ACCESS_TOKEN
    }
    res = requests.post(url, data=data)
    print(f"Paused Ad: {ad_id} → {res.status_code}")
    print("APIレスポンス:", res.text)
    return res.status_code == 200

# Slack通知
def send_slack_confirmation(ad_id, ad_name):
    if not SLACK_WEBHOOK_URL:
        print("[警告] SLACK_WEBHOOK_URLが未設定です")
        return

    message = f"✅ *広告停止実行済み通知*\n\n*広告名*: {ad_name}\n*広告ID*: `{ad_id}`\n⏸️ 停止が完了しました。"
    payload = {"text": message}
    res = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print("Slack通知結果:", res.status_code)

# メイン処理
def main():
    if not ACCESS_TOKEN:
        print("[警告] ACCESS_TOKENが未設定のため、処理を終了します")
        return

    sheet = get_sheet()
    if not sheet:
        return

    records = sheet.get_all_records()

    for row in records:
        ad_id = str(row.get("広告ID", "")).strip()
        ad_name = row.get("広告名", "")
        approval = row.get("承認", "").strip().upper()

        if approval == "YES":
            print(f"承認済み広告検出: {ad_id} ({ad_name})")
            success = pause_ad(ad_id)
            if success:
                send_slack_confirmation(ad_id, ad_name)

if __name__ == "__main__":
    main()
