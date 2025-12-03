#!/usr/bin/env python3
"""
インプレッション500以下の広告を抽出し、V2広告セットにコピーするスクリプト
"""

import os
import json
import requests
import time
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

# リトライ設定
MAX_RETRIES = 3  # 最大リトライ回数
RETRY_DELAY = 60  # リトライ間隔（秒）

# コピー履歴ファイル
COPY_HISTORY_FILE = "ad_copy_history.json"


def api_request_with_retry(method, url, max_retries=MAX_RETRIES, **kwargs):
    """レート制限エラーに対応したAPIリクエスト"""
    for attempt in range(max_retries):
        try:
            print(f"🔄 APIリクエスト試行 {attempt + 1}/{max_retries}: {method} {url[:80]}...")
            
            if method.upper() == "GET":
                res = requests.get(url, **kwargs)
            elif method.upper() == "POST":
                res = requests.post(url, **kwargs)
            else:
                raise ValueError(f"サポートされていないメソッド: {method}")
            
            print(f"   ステータスコード: {res.status_code}")
            
            # レート制限エラーをチェック
            if res.status_code == 429 or (res.status_code == 400 and "User request limit reached" in res.text):
                if attempt < max_retries - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    print(f"⚠️  レート制限エラー。{wait_time}秒待機してリトライします... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ リトライ回数上限に達しました")
                    return res
            
            # その他のエラーをチェック
            if res.status_code >= 400:
                print(f"   ⚠️  エラーレスポンス: {res.text[:200]}")
            
            return res
        
        except Exception as e:
            print(f"   ❌ 例外発生: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                print(f"⚠️  リクエストエラー。リトライします... ({attempt + 1}/{max_retries})")
                time.sleep(RETRY_DELAY)
                continue
            else:
                print(f"❌ リトライ回数上限に達しました。例外を発生させます。")
                raise
    
    print(f"❌ 全てのリトライが失敗しました")
    return None


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
        res = api_request_with_retry("GET", url, params=params)
        if res and res.status_code == 200:
            return res.json()
        else:
            print(f"❌ 広告セット詳細取得失敗: {res.status_code if res else 'None'} - {res.text if res else 'No response'}")
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
            res = api_request_with_retry("GET", url, params=params)
            if res and res.status_code == 200:
                data = res.json()
                ads.extend(data.get("data", []))
                url = data.get("paging", {}).get("next")
                params = {}  # 次のページではparamsは不要
            else:
                print(f"❌ 広告取得失敗: {res.status_code if res else 'None'} - {res.text if res else 'No response'}")
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
        res = api_request_with_retry("GET", url, params=params)
        if res and res.status_code == 200:
            data = res.json().get("data", [])
            return data[0] if data else {}
        else:
            print(f"⚠️  広告インサイト取得失敗 (ID: {ad_id}): {res.status_code if res else 'None'}")
            return {}
    except Exception as e:
        print(f"❌ 広告インサイト取得エラー (ID: {ad_id}): {e}")
        return {}


def create_v2_adset(original_adset_id, original_name):
    """V2広告セットをコピーAPIで作成"""
    v2_name = f"{original_name}V2"
    
    # 広告セットコピーAPIを使用
    url = f"https://graph.facebook.com/v21.0/{original_adset_id}/copies"
    
    payload = {
        "access_token": ACCESS_TOKEN,
        "deep_copy": "false",  # 子広告はコピーしない
        "status_option": "ACTIVE",  # コピー後のステータス
        "rename_options": json.dumps({
            "rename_strategy": "ONLY_TOP_LEVEL_RENAME",
            "rename_suffix": "V2"
        })
    }
    
    try:
        res = api_request_with_retry("POST", url, data=payload)
        if res and res.status_code == 200:
            result = res.json()
            new_adset_id = result.get("copied_adset_id")
            print(f"✅ V2広告セット作成成功: {v2_name} (ID: {new_adset_id})")
            return new_adset_id
        else:
            print(f"❌ V2広告セット作成失敗: {res.status_code if res else 'None'} - {res.text if res else 'No response'}")
            return None
    except Exception as e:
        print(f"❌ V2広告セット作成エラー: {e}")
        return None


def copy_ad_to_adset(ad_id, target_adset_id, ad_name, ad_account_id):
    """広告を指定の広告セットに新規作成（配信中状態）"""
    # 元の広告からcreative_idを取得
    ad_url = f"https://graph.facebook.com/v21.0/{ad_id}"
    ad_params = {
        "access_token": ACCESS_TOKEN,
        "fields": "creative,name"
    }
    
    try:
        # 広告詳細を取得
        ad_res = api_request_with_retry("GET", ad_url, params=ad_params)
        if not ad_res or ad_res.status_code != 200:
            print(f"  ❌ 広告詳細取得失敗: {ad_name}")
            return None
        
        ad_data = ad_res.json()
        creative_id = ad_data.get("creative", {}).get("id")
        
        if not creative_id:
            print(f"  ❌ creative_idが取得できません: {ad_name}")
            return None
        
        # 新しい広告を作成
        create_url = f"https://graph.facebook.com/v21.0/act_{ad_account_id}/ads"
        create_payload = {
            "access_token": ACCESS_TOKEN,
            "name": ad_name,
            "adset_id": target_adset_id,
            "creative": json.dumps({"creative_id": creative_id}),
            "status": "ACTIVE"  # 配信中状態で作成
        }
        
        create_res = api_request_with_retry("POST", create_url, data=create_payload)
        if create_res and create_res.status_code == 200:
            result = create_res.json()
            new_ad_id = result.get("id")
            print(f"  ✅ 広告作成成功: {ad_name} → 新ID: {new_ad_id}")
            return new_ad_id
        else:
            print(f"  ❌ 広告作成失敗: {ad_name} - {create_res.status_code if create_res else 'None'} - {create_res.text if create_res else 'No response'}")
            return None
    except Exception as e:
        print(f"  ❌ 広告作成エラー: {ad_name} - {e}")
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
    v2_adset_id = create_v2_adset(adset_id, adset_name)
    
    if not v2_adset_id:
        print("❌ V2広告セットの作成に失敗しました")
        return
    
    # 広告をコピー
    print(f"\n広告をコピー中...")
    copied_ads = []
    ad_account_id = adset_details.get("account_id")
    
    for ad in low_impression_ads:
        new_ad_id = copy_ad_to_adset(ad["id"], v2_adset_id, ad["name"], ad_account_id)
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
