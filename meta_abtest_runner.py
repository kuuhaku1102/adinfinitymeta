import requests
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")  # GSheetの共有リンク

# 認証してスプレッドシートへ接続
def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
    return sheet

# スプレッドシートに承認待ち広告を記録
def write_to_sheet(ad, cpa, image_url):
    sheet = get_sheet()
    sheet.append_row([ad['id'], ad['name'], cpa, image_url, ""])

# Slackに通知を送信
def send_slack_notice(ad, cpa, image_url):
    if not SLACK_WEBHOOK_URL:
        print("⚠️ SLACK_WEBHOOK_URL が未設定です。通知をスキップします。")
        return

    text = f"""*📣 Meta広告通知*

*広告名*: {ad['name']}
*CPA*: ¥{cpa}
*広告ID*: `{ad['id']}`
*画像URL*: {image_url}

👉 [広告停止の承認はこちら]({SPREADSHEET_URL})
"""
    payload = {"text": text}
    res = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print("📨 Slack通知ステータス:", res.status_code)
    print("📨 Slackレスポンス:", res.text)

# 広告取得
def fetch_ad_ids(account_id):
    url = f"https://graph.facebook.com/v19.0/{account_id}/ads"
    params = {"fields": "id,name", "limit": 10, "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    print("📥 ステータス:", res.status_code)
    print("📥 Ads List:", res.text)
    return res.json().get("data", [])

# 広告インサイト取得
def fetch_ad_insights(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}/insights"
    params = {"fields": "impressions,clicks,spend,actions,cost_per_action_type",
              "date_preset": "last_7d",
              "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    print(f"📊 Insights for {ad_id}: {res.text}")
    return res.json().get("data", [])[0] if res.json().get("data") else {}

# サムネイル取得
def fetch_creative_image_url(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}?fields=creative{{thumbnail_url}}&access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    return res.json().get("creative", {}).get("thumbnail_url", "画像なし")

# CPA計算
def calculate_cpa(ad):
    try:
        insights = ad.get("insights", {})
        conversions = next(
            (int(a['value']) for a in insights.get("actions", []) if a["action_type"] in ["lead", "onsite_conversion.lead_grouped"]),
            0
        )
        spend = float(insights.get("spend", 0))
        if conversions == 0:
            return None
        return round(spend / conversions, 2)
    except Exception as e:
        print("💥 CPA計算エラー:", e)
        return None

# メイン
def main():
    ads = fetch_ad_ids(ACCOUNT_ID)
    ads_with_insights = []
    for ad in ads:
        insights = fetch_ad_insights(ad["id"])
        ad["insights"] = insights
        ads_with_insights.append(ad)

    ads_with_cpa = [(ad, calculate_cpa(ad)) for ad in ads_with_insights if calculate_cpa(ad) is not None]

    if not ads_with_cpa:
        print("⚠️ 成果のある広告がありません。")
        return

    ads_sorted = sorted(ads_with_cpa, key=lambda x: x[1])
    winner = ads_sorted[0][0] if ads_sorted else None

    for ad, cpa in ads_with_cpa:
        image_url = fetch_creative_image_url(ad["id"])
        print(f"[通知] {ad['name']} - CPA: {cpa}")
        send_slack_notice(ad, cpa, image_url)
        write_to_sheet(ad, cpa, image_url)

if __name__ == "__main__":
    main()
