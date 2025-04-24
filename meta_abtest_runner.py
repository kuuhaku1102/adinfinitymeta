import requests
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")

# --- Google Sheets ---
def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
    return sheet

def write_to_sheet(ad, cpa, image_url):
    sheet = get_sheet()

    # A1セルが空ならヘッダーを書き込む
    try:
        if not sheet.cell(1, 1).value or sheet.cell(1, 1).value.strip() == "":
            sheet.append_row(["広告ID", "広告名", "CPA", "画像URL", "承認"])
    except:
        # エラー時は強制的にヘッダー書き込み
        sheet.append_row(["広告ID", "広告名", "CPA", "画像URL", "承認"])

    # 実データを追記
    sheet.append_row([ad['id'], ad['name'], cpa, image_url, ""])

# --- Meta API Fetch Functions ---
def fetch_ad_ids(account_id):
    url = f"https://graph.facebook.com/v19.0/{account_id}/ads"
    params = {"fields": "id,name", "limit": 10, "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    print("\U0001F4E5 ステータス:", res.status_code)
    print("\U0001F4E5 Ads List:", res.text)
    return res.json().get("data", [])

def fetch_ad_insights(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}/insights"
    params = {
        "fields": "impressions,clicks,spend,actions,cost_per_action_type",
        "date_preset": "last_7d",
        "access_token": ACCESS_TOKEN
    }
    res = requests.get(url, params=params)
    print(f"\U0001F4CA Insights for {ad_id}:", res.text)
    return res.json().get("data", [])[0] if res.json().get("data") else {}

def fetch_ad_type(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}?fields=id,name,effective_status&access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    print(f"📋 IDタイプ確認ログ for {ad_id}:")
    print(res.text)

def fetch_creative_image_url(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}?fields=creative{{thumbnail_url}}&access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    return res.json().get("creative", {}).get("thumbnail_url", "画像なし")

def fetch_ad_details(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}"
    params = {"fields": "name,campaign_id,adset_id", "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    return res.json()

def fetch_campaign_name(campaign_id):
    url = f"https://graph.facebook.com/v19.0/{campaign_id}"
    params = {"fields": "name", "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    return res.json().get("name", "不明なキャンペーン")

def fetch_adset_name(adset_id):
    url = f"https://graph.facebook.com/v19.0/{adset_id}"
    params = {"fields": "name", "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    return res.json().get("name", "不明な広告セット")

# --- Logic ---
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
        print("\u274c CPA計算エラー:", e)
        return None

def send_slack_notice(ad, cpa, image_url):
    if not SLACK_WEBHOOK_URL:
        print("\u26a0\ufe0f SLACK_WEBHOOK_URL が未設定です。")
        return

    ad_id = ad['id']
    ad_details = fetch_ad_details(ad_id)
    campaign_name = fetch_campaign_name(ad_details.get("campaign_id", ""))
    adset_name = fetch_adset_name(ad_details.get("adset_id", ""))

    text = f"""*\U0001F4E3 Meta広告通知*

*\u30ad\u30e3\u30f3\u30da\u30fc\u30f3\u540d*: {campaign_name}
*\u5e83\u544a\u30bb\u30c3\u30c8\u540d*: {adset_name}
*\u5e83\u544a\u540d*: {ad['name']}
*CPA*: ¥{cpa}
*\u5e83\u544aID*: `{ad_id}`
*\u753b\u50cfURL*: {image_url}

\U0001f449 [\u5e83\u544a\u505c\u6b62\u306e\u627f\u8a8d\u306f\u3053\u3061\u3089]({SPREADSHEET_URL})
"""
    payload = {"text": text}
    res = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print("\U0001f4e8 Slack通知ステータス:", res.status_code)
    print("\U0001f4e8 Slackレスポンス:", res.text)

# --- Main Execution ---
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
