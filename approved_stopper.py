import os
import json
from datetime import datetime

import requests
import gspread
from slack_reaction_helper import get_approved_ads, mark_as_stopped

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

APPROVAL_FILE = "pending_approvals.json"

# 🔍 トークンの確認ログ
if ACCESS_TOKEN:
    print("トークンチェック（ACCESS_TOKENの先頭10文字）:", ACCESS_TOKEN[:10] + "***")
else:
    print("[警告] ACCESS_TOKENが未設定です")

# --- JSON Approval Management ---
def load_approvals():
    """承認データを読み込む"""
    if not os.path.exists(APPROVAL_FILE):
        print(f"[警告] {APPROVAL_FILE}が存在しません")
        return []
    try:
        with open(APPROVAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"承認データ読み込みエラー: {e}")
        return []

def save_approvals(data):
    """承認データを保存する"""
    try:
        with open(APPROVAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"承認データ保存エラー: {e}")
        return False

def get_approved_ads_from_json():
    """承認済みの広告リストをJSONから取得"""
    approvals = load_approvals()
    approved = [ad for ad in approvals if ad.get('status') == 'approved']
    print(f"✅ JSONから承認済み広告: {len(approved)}件")
    return approved

def mark_ad_as_stopped_json(ad_id):
    """広告を停止済みとしてマーク（JSON）"""
    approvals = load_approvals()
    for ad in approvals:
        if ad.get('ad_id') == ad_id and ad.get('status') == 'approved':
            ad['status'] = 'stopped'
            ad['stopped_at'] = datetime.now().isoformat()
            save_approvals(approvals)
            print(f"✅ 広告 {ad_id} を停止済みにマークしました")
            return True
    return False

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

    print("=== Slackリアクションから承認済み広告を読み取り ===")
    
    # Slackリアクションから承認済み広告を取得
    try:
        approved_ads_from_slack = get_approved_ads()
    except Exception as e:
        print(f"[警告] Slackリアクションの読み取りに失敗: {e}")
        approved_ads_from_slack = []
    
    # JSONファイルからも承認済み広告を取得（Web UI互換性）
    print("\n=== JSONファイルから承認済み広告を読み取り ===")
    approved_ads_from_json = get_approved_ads_from_json()
    
    # 両方を統合
    all_approved_ads = approved_ads_from_slack + approved_ads_from_json
    
    if not all_approved_ads:
        print("承認済みの広告がありません")
        
        # Google Sheetsをフォールバックとして確認
        print("\n=== Google Sheetsをフォールバックとして確認 ===")
        sheet = get_sheet()
        if sheet:
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
        return
    
    # 承認済み広告を処理
    print(f"\n=== {len(all_approved_ads)}件の承認済み広告を処理 ===")
    for ad in all_approved_ads:
        ad_id = ad.get('ad_id')
        ad_name = ad.get('ad_name', '')
        
        print(f"承認済み広告検出: {ad_id} ({ad_name})")
        success = pause_ad(ad_id)
        if success:
            send_slack_confirmation(ad_id, ad_name)
            # Slackリアクション経由の場合
            if 'message_ts' in ad:
                mark_as_stopped(ad_id)
            # JSON経由の場合
            else:
                mark_ad_as_stopped_json(ad_id)

if __name__ == "__main__":
    main()
