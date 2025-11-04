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

# 固定設定
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
ACCOUNT_IDS = os.getenv("ACCOUNT_IDS")
CAMPAIGN_IDS = "120231962646350484,120230617419590484"  # ← 固定のキャンペーンID
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")

if not ACCESS_TOKEN:
    print("[警告] ACCESS_TOKENが未設定のため、Meta APIへのアクセスはスキップされます")

# --- Account IDの取得 ---
def get_account_ids():
    if ACCOUNT_IDS:
        return [aid.strip() for aid in ACCOUNT_IDS.split(',') if aid.strip()]
    elif ACCOUNT_ID:
        return [ACCOUNT_ID]
    else:
        print("[警告] ACCOUNT_IDまたはACCOUNT_IDSが未設定です")
        return []

# --- Campaign IDの取得 ---
def get_campaign_ids():
    if CAMPAIGN_IDS:
        return [cid.strip() for cid in CAMPAIGN_IDS.split(',') if cid.strip()]
    return []

# --- Google Sheets ---
def get_sheet():
    if not SPREADSHEET_URL:
        print("[警告] SPREADSHEET_URLが未設定のため、スプレッドシートへの書き込みをスキップします")
        return None

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SPREADSHEET_URL).sheet1
        return sheet
    except Exception as e:
        print("[警告] スプレッドシートへの接続に失敗しました:", e)
        return None

def write_rows_to_sheet(rows):
    sheet = get_sheet()
    if not sheet:
        return

    if not sheet.row_values(1):
        sheet.append_row(["広告キャンペーン", "広告グループ", "広告ID", "広告名", "CPA", "画像URL"])
    sheet.append_rows(rows, value_input_option='USER_ENTERED')

# --- Meta API Fetch Functions ---
def fetch_ad_ids(account_id, campaign_ids=None):
    if not ACCESS_TOKEN:
        return []

    ads = []
    if campaign_ids and len(campaign_ids) > 0:
        for cid in campaign_ids:
            url = f"https://graph.facebook.com/v19.0/{cid}/ads"
            params = [
                ("fields", "id,name,effective_status"),
                ("limit", 50),
                ("access_token", ACCESS_TOKEN),
                ("effective_status", "['ACTIVE']")  # 元のまま使用
            ]
            res = requests.get(url, params=params)
            print(f"キャンペーン {cid} の広告取得ステータス:", res.status_code)
            print("レスポンス内容:", res.text)  # ← ここで詳細確認
            if res.status_code == 200:
                ads.extend(res.json().get("data", []))
        return ads
    else:
        print(f"[スキップ] campaign_ids が空または未指定のため、アカウント {account_id} の広告取得をスキップ")
        return []

def fetch_ad_insights(ad_id):
    if not ACCESS_TOKEN:
        return {}

    url = f"https://graph.facebook.com/v19.0/{ad_id}/insights"
    params = {
        "fields": "impressions,clicks,spend,actions,cost_per_action_type",
        "date_preset": "last_14d",
        "access_token": ACCESS_TOKEN
    }
    res = requests.get(url, params=params)
    print(f"📊 Insights for {ad_id}:", res.text)
    return res.json().get("data", [])[0] if res.json().get("data") else {}

def fetch_creative_image_url(ad_id):
    if not ACCESS_TOKEN:
        return "画像なし"

    url = f"https://graph.facebook.com/v19.0/{ad_id}?fields=creative{{thumbnail_url}}&access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    return res.json().get("creative", {}).get("thumbnail_url", "画像なし")

def fetch_ad_details(ad_id):
    if not ACCESS_TOKEN:
        return {}

    url = f"https://graph.facebook.com/v19.0/{ad_id}"
    params = {"fields": "name,campaign_id,adset_id", "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    return res.json()

def fetch_campaign_name(campaign_id):
    if not ACCESS_TOKEN:
        return "不明なキャンペーン"

    url = f"https://graph.facebook.com/v19.0/{campaign_id}"
    params = {"fields": "name", "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    return res.json().get("name", "不明なキャンペーン")

def fetch_adset_name(adset_id):
    if not ACCESS_TOKEN:
        return "不明な広告セット"

    url = f"https://graph.facebook.com/v19.0/{adset_id}"
    params = {"fields": "name", "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    return res.json().get("name", "不明な広告セット")

# --- Metrics Calculation ---
def calculate_metrics(ad):
    try:
        insights = ad.get("insights", {})
        conversions = next(
            (int(a['value']) for a in insights.get("actions", [])
             if a["action_type"] in ["lead", "onsite_conversion.lead_grouped"]),
            0
        )
        clicks = int(insights.get("clicks", 0))
        impressions = int(insights.get("impressions", 0))
        spend = float(insights.get("spend", 0))
        cpa = round(spend / conversions, 2) if conversions > 0 else None
        ctr = round(clicks / impressions, 4) if impressions > 0 else 0
        return cpa, ctr
    except Exception as e:
        print("❌ 指標計算エラー:", e)
        return None, 0

def post_slack_message(text):
    if not SLACK_WEBHOOK_URL:
        print("[警告] SLACK_WEBHOOK_URLが未設定です")
        return False

    payload = {"text": text}
    res = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print("Slack通知結果:", res.status_code)
    return res.status_code == 200


def send_slack_notice(ad, cpa, image_url, label):
    if not ACCESS_TOKEN:
        print("[警告] ACCESS_TOKENが未設定のため、広告詳細を取得できずSlack通知をスキップします")
        return

    ad_id = ad['id']
    ad_details = fetch_ad_details(ad_id)
    campaign_name = fetch_campaign_name(ad_details.get("campaign_id", ""))
    adset_name = fetch_adset_name(ad_details.get("adset_id", ""))

    text = f"""*📣 Meta広告通知 [{label}]*

*キャンペーン名*: {campaign_name}
*広告セット名*: {adset_name}
*広告名*: {ad['name']}
*CPA*: ¥{cpa if cpa is not None else 'N/A'}
*広告ID*: `{ad_id}`
*画像URL*: {image_url}

👉 [広告停止の承認はこちら]({SPREADSHEET_URL})
"""
    post_slack_message(text)


def notify_no_stop_candidates(account_id, reason=None):
    message = ["*📣 Meta広告通知 [停止対象なし]*", "", f"*アカウントID*: {account_id}", "指定された条件で停止対象の広告は見つかりませんでした。"]
    if reason:
        message.extend(["", f"補足: {reason}"])
    post_slack_message("\n".join(message))

# --- 広告評価ロジック ---
def evaluate_account(account_id):
    print(f"=== {account_id} の広告を評価中 ===")
    campaign_ids = get_campaign_ids()
    if not campaign_ids:
        print(f"[スキップ] {account_id} の広告は、キャンペーンIDが未指定のため評価対象外")
        notify_no_stop_candidates(account_id, "キャンペーンIDが未指定です")
        return

    ads = fetch_ad_ids(account_id, campaign_ids=campaign_ids)

    if not ads:
        notify_no_stop_candidates(account_id, "アクティブな広告を取得できませんでした")
        return

    ads_with_insights = []
    for ad in ads:
        insights = fetch_ad_insights(ad["id"])
        ad["insights"] = insights
        ads_with_insights.append(ad)

    ads_with_metrics = []
    for ad in ads_with_insights:
        cpa, ctr = calculate_metrics(ad)
        ads_with_metrics.append((ad, cpa, ctr))

    with_cpa = [entry for entry in ads_with_metrics if entry[1] is not None]
    without_cpa = [entry for entry in ads_with_metrics if entry[1] is None]

    top_ctr_no_cv = sorted(without_cpa, key=lambda x: x[2], reverse=True)[:5]
    winners = [entry[0] for entry in sorted(with_cpa, key=lambda x: x[1])[:1] + top_ctr_no_cv]

    rows_to_write = []
    for ad, cpa, ctr in ads_with_metrics:
        if ad not in winners:
            image_url = fetch_creative_image_url(ad["id"])
            print(f"[通知] {ad['name']} - CPA: {cpa} CTR: {ctr}")
            send_slack_notice(ad, cpa, image_url, label="STOP候補")

            ad_details = fetch_ad_details(ad['id'])
            campaign_name = fetch_campaign_name(ad_details.get("campaign_id", ""))
            adset_name = fetch_adset_name(ad_details.get("adset_id", ""))

            rows_to_write.append([
                campaign_name,
                adset_name,
                ad['id'],
                ad['name'],
                cpa if cpa is not None else "N/A",
                image_url
            ])

    if rows_to_write:
        write_rows_to_sheet(rows_to_write)
    else:
        notify_no_stop_candidates(account_id)

# --- Main Entry Point ---
def main():
    if not ACCESS_TOKEN:
        print("[警告] ACCESS_TOKENが未設定のため、評価処理を終了します")
        return

    for aid in get_account_ids():
        evaluate_account(aid)

if __name__ == "__main__":
    main()
