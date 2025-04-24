import requests
import os

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# 広告一覧を取得
def fetch_ad_ids(account_id):
    url = f"https://graph.facebook.com/v19.0/{account_id}/ads"
    params = {
        "fields": "id,name",
        "limit": 10,
        "access_token": ACCESS_TOKEN
    }
    res = requests.get(url, params=params)
    print("📥 ステータス:", res.status_code)
    print("📥 Ads List:", res.text)
    return res.json().get("data", [])

# 広告ごとのインサイト（成果情報）を取得
def fetch_ad_insights(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}/insights"
    params = {
        "fields": "impressions,clicks,spend,actions,cost_per_action_type",
        "date_preset": "last_7d",
        "access_token": ACCESS_TOKEN
    }
    res = requests.get(url, params=params)
    print(f"📊 Insights for {ad_id}: {res.text}")
    data = res.json().get("data", [])
    return data[0] if data else {}

# 広告のサムネイル画像URLを取得
def fetch_creative_image_url(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}?fields=creative{{thumbnail_url}}&access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    data = res.json()
    return data.get("creative", {}).get("thumbnail_url", "画像なし")

# CPAを計算
def calculate_cpa(ad):
    try:
        insights = ad.get("insights", {})
        conversions = next((int(a['value']) for a in insights.get("actions", []) if a["action_type"] in ["lead", "onsite_conversion.lead_grouped"]), 0)
        spend = float(insights.get("spend", 0))
        return round(spend / conversions, 2) if conversions > 0 else float('inf')
    except Exception as e:
        print("💥 CPA計算エラー:", e)
        return float('inf')

# 広告を停止
def pause_ad(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}"
    data = {
        "status": "PAUSED",
        "access_token": ACCESS_TOKEN
    }
    res = requests.post(url, data=data)
    print(f"⏸️ Paused Ad: {ad_id} → {res.status_code}")

# Slack通知を送信
def send_slack_notice(ad, cpa, image_url):
    if not SLACK_WEBHOOK_URL:
        print("⚠️ SLACK_WEBHOOK_URL が未設定です。通知をスキップします。")
        return

    text = f"""*⏸️ 停止候補広告*

*広告名*: {ad['name']}
*CPA*: ¥{cpa}
*広告ID*: `{ad['id']}`
*画像URL*: {image_url}

⚠️ この広告を停止候補として通知します。
"""
    payload = {"text": text}
    res = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print("📨 Slack通知結果:", res.status_code)

# メイン処理
def main():
    ads = fetch_ad_ids(ACCOUNT_ID)
    ads_with_insights = []
    for ad in ads:
        insights = fetch_ad_insights(ad["id"])
        ad["insights"] = insights
        ads_with_insights.append(ad)

    ads_with_cpa = [(ad, calculate_cpa(ad)) for ad in ads_with_insights]
    ads_sorted = sorted(ads_with_cpa, key=lambda x: x[1])
    winner = ads_sorted[0][0] if ads_sorted else None

    for ad, cpa in ads_with_cpa:
        image_url = fetch_creative_image_url(ad["id"])
        if ad != winner:
            print(f"[STOP] {ad['name']} - CPA: {cpa}")
            send_slack_notice(ad, cpa, image_url)
            pause_ad(ad["id"])
        else:
            print(f"[KEEP] {ad['name']} - CPA: {cpa}")

if __name__ == "__main__":
    main()
