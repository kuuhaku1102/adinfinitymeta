import requests
import os

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

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

def calculate_cpa(ad):
    try:
        insights = ad.get("insights", {})
        conversions = next((int(a['value']) for a in insights.get("actions", []) if a["action_type"] == "offsite_conversion"), 0)
        spend = float(insights.get("spend", 0))
        return round(spend / conversions, 2) if conversions > 0 else float('inf')
    except Exception as e:
        print("💥 CPA計算エラー:", e)
        return float('inf')

def pause_ad(ad_id):
    url = f"https://graph.facebook.com/v19.0/{ad_id}"
    data = {
        "status": "PAUSED",
        "access_token": ACCESS_TOKEN
    }
    res = requests.post(url, data=data)
    print(f"⏸️ Paused Ad: {ad_id} → {res.status_code}")

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
        if ad != winner:
            print(f"[STOP] {ad['name']} - CPA: {cpa}")
            pause_ad(ad["id"])
        else:
            print(f"[KEEP] {ad['name']} - CPA: {cpa}")

if __name__ == "__main__":
    main()
