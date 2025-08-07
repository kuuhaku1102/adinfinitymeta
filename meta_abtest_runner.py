import requests
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 環境変数の読み込み（固定に書き換えたバージョン）
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
ACCOUNT_IDS = os.getenv("ACCOUNT_IDS")
CAMPAIGN_IDS = "120230617419590484"  # ← 固定されたキャンペーンID
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")

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
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
    return sheet

def write_to_sheet(ad, cpa, image_url):
    sheet = get_sheet()
    if not sheet.row_values(1):
        sheet.append_row(["広告キャンペーン", "広告グループ", "広告ID", "広告名", "CPA", "画像URL"])
    
    ad_details = fetch_ad_details(ad['id'])
    campaign_name = fetch_campaign_name(ad_details.get("campaign_id", ""))
    adset_name = fetch_adset_name(ad_details.get("adset_id", ""))

    sheet.append_row([
        campaign_name,
        adset_name,
        ad['id'],
        ad['name'],
        cpa if cpa is not None else "N/A",
        image_url
    ])

def write_rows_to_sheet(rows):
    sheet = get_sheet()
    if not sheet.row_values(1):
        sheet.append_row(["広告キャンペーン", "広告グループ", "広告ID", "広告名", "CPA", "画像URL"])
    sheet.append_rows(rows, value_input_option='USER_ENTERED')

# --- Meta API Fetch Functions ---
def fetch_ad_ids(account_id, campaign_ids=None):
    ads = []
    if campaign_ids is not None and len(campaign_ids) > 0:
        for cid in campaign_ids:
            url = f"https://graph.facebook.com/v19.0/{cid}/ads"
            params = [
                ("fields", "id,name,effective_status"),
                ("limit", 50),
                ("access_token", ACCESS_TOKEN),
                ("effective_status", "['ACTIVE']")
            ]
            res = requests.get(url, params=params)
            print(f"キャンペーン {cid} の広告取得ステータス:", res.status_code)
            ads.extend(res.json().get("data", []))
        return ads
    else:
        print(f"[スキップ] campaign_ids が空または未指定のため、アカウント {account_id} の広告取得をスキップ")
        return []

def fetch_ad_insights(ad_id):
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

def send_slack_notice(ad, cpa, image_url, label):
    if not SLACK_WEBHOOK_URL:
        print("[警告] SLACK_WEBHOOK_URLが未設定です")
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
    payload = {"text": text}
    res = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print("Slack通知結果:", res.status_code)

# --- 各アカウントの評価 ---
def evaluate_account(account_id):
    print(f"=== {account_id} の広告を評価中 ===")

    campaign_ids = get_campaign_ids()
    if not campaign_ids:
        print(f"[スキップ] {account_id} の広告は、キャンペーンIDが未指定のため評価対象外")
        return

    ads = fetch_ad_ids(account_id, campaign_ids=campaign_ids)

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

# --- Main Entry Point ---
def main():
    for aid in get_account_ids():
        evaluate_account(aid)

if __name__ == "__main__":
    main()
