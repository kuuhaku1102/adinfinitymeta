import requests
import os
import json

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

# 各広告の成果インサイト取得
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

# クリエイティブ画像URL取得
def fetch_creative_image_url(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}?fields=creative{{thumbnail_url}}&access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    data = res.json()
    return data.get("creative", {}).get("thumbnail_url", "画像なし")

# CPA計算（CV=0なら評価対象外）
def calculate_cpa(ad):
    try:
        insights = ad.get("insights", {})
        actions = insights.get("actions", [])
        conversions = next(
            (int(a['value']) for a in actions if a["action_type"] in ["lead", "onsite_conversion.lead_grouped"]),
            0
        )
        spend = float(insights.get("spend", 0))
        if conversions == 0:
            return None  # 成果なし → 評価除外
        return round(spend / conversions, 2)
    except Exception as e:
        print("💥 CPA計算エラー:", e)
        return None

# 広告停止
def pause_ad(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}"
    data = {
        "status": "PAUSED",
        "access_token": ACCESS_TOKEN
    }
    res = requests.post(url, data=data)
    print(f"⏸️ Paused Ad: {ad_id} → {res.status_code}")

# Slack通知
def send_slack_notice(ad, cpa, image_url):
    if not SLACK_WEBHOOK_URL:
        print("⚠️ SLACK_WEBHOOK_URL が未設定です。通知をスキップします。")
        return

    ad_id = ad['id']
    text = f"""*📣 Meta広告通知*

*広告名*: {ad['name']}
*CPA*: ¥{cpa}
*広告ID*: `{ad_id}`
*画像URL*: {image_url}

⚠️ 成果ベースで評価された広告の情報です。
"""
    payload = {"text": text}
    res = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print("📨 Slack通知ステータス:", res.status_code)
    print("📨 Slackレスポンス:", res.text)

# メイン実行
def main():
    ads = fetch_ad_ids(ACCOUNT_ID)
    ads_with_insights = []
    for ad in ads:
        insights = fetch_ad_insights(ad["id"])
        ad["insights"] = insights
        ads_with_insights.append(ad)

    # 成果あり（CV > 0）の広告だけ評価対象
    ads_with_cpa = [
        (ad, cpa)
        for ad in ads_with_insights
        if (cpa := calculate_cpa(ad)) is not None
    ]

    if not ads_with_cpa:
        print("⚠️ 成果のある広告がありません。")
        return

    ads_sorted = sorted(ads_with_cpa, key=lambda x: x[1])
    winner = ads_sorted[0][0] if ads_sorted else None

    for ad, cpa in ads_with_cpa:
        image_url = fetch_creative_image_url(ad["id"])
        if ad == winner:
            print(f"[KEEP] {ad['name']} - CPA: {cpa}")
            send_slack_notice(ad, cpa, image_url)
        else:
            print(f"[STOP] {ad['name']} - CPA: {cpa}")
            send_slack_notice(ad, cpa, image_url)
            pause_ad(ad["id"])

if __name__ == "__main__":
    main()
