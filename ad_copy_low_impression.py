#!/usr/bin/env python3
"""
インプレッション500以下の広告を抽出し、V2広告セットにコピーするスクリプト
"""

import os
import json
import requests
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    print("[警告] python-dotenvが未インストールのため、.env読み込みをスキップします")
    load_dotenv = lambda: None

load_dotenv()

# 環境変数
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN") or os.getenv("META_ACCESS_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

# 設定
IMPRESSION_THRESHOLD = 500  # インプレッション閾値
MIN_AD_COUNT = 4  # 最小広告数
DATE_RANGE_DAYS = 14  # 使用しない（全期間で判定）

# コピー履歴ファイル
COPY_HISTORY_FILE = "ad_copy_history.json"


def load_copy_history():
    """コピー履歴を読み込み"""
    if os.path.exists(COPY_HISTORY_FILE):
        try:
            with open(COPY_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"コピー履歴読み込みエラー: {e}")
    return []


def save_copy_history(history):
    """コピー履歴を保存"""
    try:
        with open(COPY_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"コピー履歴保存エラー: {e}")
        return False


def fetch_adset_details(adset_id):
    """広告セットの詳細情報を取得"""
    url = f"https://graph.facebook.com/v21.0/{adset_id}"
    params = {
        "access_token": ACCESS_TOKEN,
        "fields": "name,campaign_id,account_id,targeting,bid_amount,billing_event,optimization_goal,daily_budget,lifetime_budget,status"
    }
    
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"❌ 広告セット詳細取得失敗: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        print(f"❌ 広告セット詳細取得エラー: {e}")
        return None


def fetch_ads_in_adset(adset_id):
    """広告セット内の広告を取得"""
    url = f"https://graph.facebook.com/v21.0/{adset_id}/ads"
    params = {
        "access_token": ACCESS_TOKEN,
        "fields": "id,name,status,creative",
        "limit": 100
    }
    
    ads = []
    try:
        while url:
            res = requests.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                ads.extend(data.get("data", []))
                url = data.get("paging", {}).get("next")
                params = {}  # 次のページではparamsは不要
            else:
                print(f"❌ 広告取得失敗: {res.status_code} - {res.text}")
                break
    except Exception as e:
        print(f"❌ 広告取得エラー: {e}")
    
    return ads


def fetch_ad_insights(ad_id, days=14):
    """広告のインサイトを取得（全期間）"""
    # 全期間のデータを取得（過去2年間で取得）
    since = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    until = datetime.now().strftime("%Y-%m-%d")
    
    url = f"https://graph.facebook.com/v21.0/{ad_id}/insights"
    params = {
        "access_token": ACCESS_TOKEN,
        "time_range": json.dumps({"since": since, "until": until}),
        "fields": "impressions,spend,clicks,actions"
    }
    
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json().get("data", [])
            return data[0] if data else {}
        else:
            print(f"⚠️  広告インサイト取得失敗 (ID: {ad_id}): {res.status_code}")
            return {}
    except Exception as e:
        print(f"❌ 広告インサイト取得エラー (ID: {ad_id}): {e}")
        return {}


def create_v2_adset(original_adset):
    """V2広告セットを作成"""
    original_name = original_adset.get("name", "")
    v2_name = f"{original_name}V2"
    campaign_id = original_adset.get("campaign_id")
    account_id = original_adset.get("account_id")
    
    print(f"デバッグ: campaign_id = {campaign_id}")
    print(f"デバッグ: account_id = {account_id}")
    print(f"デバッグ: original_adset keys = {list(original_adset.keys())}")
    
    if not campaign_id:
        print("❌ campaign_idが取得できませんでした")
        return None
    
    if not account_id:
        print("❌ account_idが取得できませんでした")
        return None
    
    # 正しいエンドポイント: /act_{ad_account_id}/adsets
    url = f"https://graph.facebook.com/v21.0/act_{account_id}/adsets"
    
    payload = {
        "access_token": ACCESS_TOKEN,
        "name": v2_name,
        "campaign_id": campaign_id,
        "targeting": json.dumps(original_adset.get("targeting", {})),
        "billing_event": original_adset.get("billing_event", "IMPRESSIONS"),
        "optimization_goal": original_adset.get("optimization_goal", "REACH"),
        "status": "ACTIVE"
    }
    
    # 予算設定
    if "daily_budget" in original_adset and original_adset["daily_budget"]:
        payload["daily_budget"] = original_adset["daily_budget"]
    elif "lifetime_budget" in original_adset and original_adset["lifetime_budget"]:
        payload["lifetime_budget"] = original_adset["lifetime_budget"]
    
    # 入札額
    if "bid_amount" in original_adset and original_adset["bid_amount"]:
        payload["bid_amount"] = original_adset["bid_amount"]
    
    try:
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            result = res.json()
            new_adset_id = result.get("id")
            print(f"✅ V2広告セット作成成功: {v2_name} (ID: {new_adset_id})")
            return new_adset_id
        else:
            print(f"❌ V2広告セット作成失敗: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        print(f"❌ V2広告セット作成エラー: {e}")
        return None


def copy_ad_to_adset(ad_id, target_adset_id, ad_name):
    """広告を指定の広告セットにコピー（配信中状態）"""
    url = f"https://graph.facebook.com/v21.0/{ad_id}/copies"
    
    payload = {
        "access_token": ACCESS_TOKEN,
        "adset_id": target_adset_id,
        "status_option": "ACTIVE"  # 配信中状態でコピー
    }
    
    try:
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            result = res.json()
            new_ad_id = result.get("copied_ad_id")
            print(f"  ✅ 広告コピー成功: {ad_name} → 新ID: {new_ad_id}")
            return new_ad_id
        else:
            print(f"  ❌ 広告コピー失敗: {ad_name} - {res.status_code} - {res.text}")
            return None
    except Exception as e:
        print(f"  ❌ 広告コピーエラー: {ad_name} - {e}")
        return None


def pause_adset(adset_id, adset_name):
    """広告セットを停止"""
    url = f"https://graph.facebook.com/v21.0/{adset_id}"
    
    payload = {
        "access_token": ACCESS_TOKEN,
        "status": "PAUSED"
    }
    
    try:
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            print(f"✅ 広告セット停止成功: {adset_name}")
            return True
        else:
            print(f"❌ 広告セット停止失敗: {res.status_code} - {res.text}")
            return False
    except Exception as e:
        print(f"❌ 広告セット停止エラー: {e}")
        return False


def send_slack_notification(message):
    """Slackに通知を送信"""
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        print("[警告] Slack設定が未設定のため、通知をスキップします")
        return
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": SLACK_CHANNEL_ID,
        "text": message
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200 and res.json().get("ok"):
            print("✅ Slack通知送信成功")
        else:
            print(f"❌ Slack通知送信失敗: {res.text}")
    except Exception as e:
        print(f"❌ Slack通知送信エラー: {e}")


def process_adset(adset_id):
    """広告セットを処理"""
    print(f"\n{'='*60}")
    print(f"広告セット処理開始: {adset_id}")
    print(f"{'='*60}\n")
    
    # 広告セット詳細を取得
    adset_details = fetch_adset_details(adset_id)
    if not adset_details:
        print("❌ 広告セット詳細の取得に失敗しました")
        return
    
    adset_name = adset_details.get("name", "")
    print(f"広告セット名: {adset_name}")
    
    # 広告を取得
    ads = fetch_ads_in_adset(adset_id)
    active_ads = [ad for ad in ads if ad.get("status") == "ACTIVE"]
    print(f"広告数: {len(ads)}件 (ACTIVE: {len(active_ads)}件)")
    
    if not ads:
        print("⚠️  広告が見つかりませんでした")
        return
    
    # インプレッション500以下の広告を抽出
    low_impression_ads = []
    
    print("\n広告のインサイトを取得中...")
    for ad in ads:
        ad_id = ad["id"]
        ad_name = ad["name"]
        
        insights = fetch_ad_insights(ad_id)  # 全期間で取得
        impressions = int(insights.get("impressions", 0))
        
        print(f"  - {ad_name}: {impressions} imp")
        
        if impressions <= IMPRESSION_THRESHOLD:
            low_impression_ads.append({
                "id": ad_id,
                "name": ad_name,
                "impressions": impressions
            })
    
    print(f"\nインプレッション{IMPRESSION_THRESHOLD}以下の広告: {len(low_impression_ads)}件")
    
    # 広告数チェック
    if len(low_impression_ads) < MIN_AD_COUNT:
        message = f"⚠️  広告数が{MIN_AD_COUNT}個未満のためスキップ\n\n広告セット: {adset_name}\n対象広告数: {len(low_impression_ads)}件"
        print(f"\n{message}")
        send_slack_notification(message)
        return
    
    # コピー後に元の広告セットに残る広告数をチェック（全広告で判断）
    remaining_ads_count = len(ads) - len(low_impression_ads)
    print(f"\nコピー後に残る広告数: {remaining_ads_count}件（全広告で判断）")
    
    if remaining_ads_count == 0:
        message = f"⚠️  広告コピースキップ\n\n*広告セット:* {adset_name}\n*理由:* コピー後に広告が0個になるため\n*対象広告数:* {len(low_impression_ads)}件"
        print(f"\n{message}")
        send_slack_notification(message)
        return
    
    # V2広告セットを作成
    print(f"\nV2広告セットを作成中...")
    v2_adset_id = create_v2_adset(adset_details)
    
    if not v2_adset_id:
        print("❌ V2広告セットの作成に失敗しました")
        return
    
    # 広告をコピー
    print(f"\n広告をコピー中...")
    copied_ads = []
    
    for ad in low_impression_ads:
        new_ad_id = copy_ad_to_adset(ad["id"], v2_adset_id, ad["name"])
        if new_ad_id:
            copied_ads.append({
                "original_id": ad["id"],
                "new_id": new_ad_id,
                "name": ad["name"],
                "impressions": ad["impressions"]
            })
    
    # コピー履歴を保存
    history = load_copy_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "original_adset_id": adset_id,
        "original_adset_name": adset_name,
        "v2_adset_id": v2_adset_id,
        "v2_adset_name": f"{adset_name}V2",
        "copied_ads": copied_ads
    })
    save_copy_history(history)
    
    # Slack通知
    message = f"""✅ 広告コピー完了

*元の広告セット:* {adset_name}
*新しい広告セット:* {adset_name}V2
*コピーした広告数:* {len(copied_ads)}件

*コピーした広告:*
"""
    for ad in copied_ads:
        message += f"\n  • {ad['name']} ({ad['impressions']} imp)"
    
    print(f"\n{message}")
    send_slack_notification(message)
    
    print(f"\n{'='*60}")
    print("処理完了")
    print(f"{'='*60}\n")


def main():
    """メイン処理"""
    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKENが未設定です")
        return
    
    # 広告セットIDを指定（環境変数または引数から取得）
    adset_id = os.getenv("TARGET_ADSET_ID")
    
    if not adset_id:
        print("❌ TARGET_ADSET_IDが未設定です")
        print("使い方: TARGET_ADSET_ID=123456789 python3 ad_copy_low_impression.py")
        return
    
    process_adset(adset_id)


if __name__ == "__main__":
    main()
