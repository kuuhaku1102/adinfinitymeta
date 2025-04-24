import requests
import os

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")  # GitHub Actions側で固定的に指定している

def fetch_ads(account_id):
    url = f"https://graph.facebook.com/v19.0/{account_id}/ads"
    params = {
        "fields": "id,ad_name,insights.date_preset(last_7d){impressions,clicks,spend,actions,cost_per_action_type}",
        "limit": 10,
        "access_token": ACCESS_TOKEN
    }

    res = requests.get(url, params=params)
    print("📥 ステータスコード:", res.status_code)
    print("📥 レスポンス本文:")
    print(res.text)

    try:
        data = res.json()
        ads = data.get("data", [])
        print(f"📊 広告取得件数: {len(ads)}")
        return ads
    except Exception as e:
        print("💥 JSONエラー:", e)
        return []

def calculate_cpa(ad):
    try:
        insights = ad.get("insights", [{}])[0]
        conversions = next((int(a['value']) for a in insights.get("actions", []) if a["action_type"] == "offsite_conversion"), 0)
        spend = float(insights.get("spend", 0))
        return round(spend / conversions, 2) if conversions > 0 else float('inf')
    except Exception as e:
        print("CPA計算エラー:", e)
        return float('inf')


def pause_ad(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}"
    data = {
        "status": "PAUSED",
        "access_token": ACCESS_TOKEN
    }
    res = requests.post(url, data=data)
    print(f"Paused Ad: {ad_id} → {res.status_code}")

ads = fetch_ads(ACCOUNT_ID)

ads_with_cpa = [(ad, calculate_cpa(ad)) for ad in ads]
ads_sorted = sorted(ads_with_cpa, key=lambda x: x[1])
winner = ads_sorted[0][0] if ads_sorted else None

for ad, cpa in ads_with_cpa:
    if ad != winner:
        print(f"[STOP] {ad['ad_name']} - CPA: {cpa}")
        pause_ad(ad["id"])
    else:
        print(f"[KEEP] {ad['ad_name']} - CPA: {cpa}")
