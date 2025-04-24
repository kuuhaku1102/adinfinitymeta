import requests
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Google Sheets接続
def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
    return sheet

# Meta広告を停止する
def pause_ad(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}"
    data = {
        "status": "PAUSED",
        "access_token": ACCESS_TOKEN
    }
    res = requests.post(url, data=data)
    print(f"⏸️ Paused Ad: {ad_id} → {res.status_code}")
    print("📥 APIレスポンス:", res.text)  # ← 追加
    return res.status_code == 200

# Slack通知
def send_slack_confirmation(ad_id, ad_name):
    if not SLACK_WEBHOOK_URL:
        print("\u26a0\ufe0f SLACK_WEBHOOK_URLが未設定です")
        return

    message = f"\u2705 *広告停止実行済み通知*\n\n*広告名*: {ad_name}\n*広告ID*: `{ad_id}`\n\u23f8\ufe0f 停止が完了しました。"
    payload = {"text": message}
    res = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print("\U0001F4E8 Slack通知結果:", res.status_code)

# メイン処理
def main():
    sheet = get_sheet()
    records = sheet.get_all_records()

    for row in records:
        ad_id = str(row.get("広告ID", "")).strip()
        ad_name = row.get("広告名", "")
        approval = row.get("承認", "").strip().upper()

        if approval == "YES":
            print(f"\u2709 承認済み広告検出: {ad_id} ({ad_name})")
            success = pause_ad(ad_id)
            if success:
                send_slack_confirmation(ad_id, ad_name)

if __name__ == "__main__":
    main()
