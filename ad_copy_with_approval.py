#!/usr/bin/env python3
"""
Slack承認フロー付き広告コピースクリプト

広告セットごとにSlackで承認を求め、承認されたもののみコピーする
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from slack_reaction_helper import send_slack_message_with_bot

# 環境変数を読み込み
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
CAMPAIGN_IDS = os.getenv("CAMPAIGN_IDS", "").split(",")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

APPROVAL_FILE = "ad_copy_approvals.json"
COPY_HISTORY_FILE = "ad_copy_history.json"

def load_copy_history():
    """コピー履歴を読み込み"""
    if os.path.exists(COPY_HISTORY_FILE):
        try:
            with open(COPY_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  コピー履歴読み込みエラー: {e}")
    return []

def is_already_copied(adset_id, copy_history):
    """広告セットが既にコピー済みかチェック"""
    for record in copy_history:
        if record.get("original_adset_id") == adset_id:
            return True
    return False

def fetch_campaign_info(campaign_id):
    """キャンペーン情報を取得"""
    if not ACCESS_TOKEN:
        return None
    
    url = f"https://graph.facebook.com/v19.0/{campaign_id}"
    params = {
        "fields": "id,name,effective_status",
        "access_token": ACCESS_TOKEN
    }
    
    try:
        res = requests.get(url, params=params)
        data = res.json()
        
        if "error" in data:
            return None
        
        return data
    
    except Exception as e:
        return None

def fetch_adsets_from_campaign(campaign_id):
    """キャンペーンから全広告セットを取得"""
    if not ACCESS_TOKEN:
        return []
    
    url = f"https://graph.facebook.com/v19.0/{campaign_id}/adsets"
    params = {
        "fields": "id,name,effective_status",
        "access_token": ACCESS_TOKEN,
        "limit": 100
    }
    
    try:
        res = requests.get(url, params=params)
        data = res.json()
        
        if "error" in data:
            return []
        
        return data.get("data", [])
    
    except Exception as e:
        return []

def count_low_impression_ads(adset_id):
    """インプレッション500以下の広告数をカウント"""
    if not ACCESS_TOKEN:
        return 0
    
    # 広告を取得
    url = f"https://graph.facebook.com/v19.0/{adset_id}/ads"
    params = {
        "fields": "id,name,effective_status",
        "access_token": ACCESS_TOKEN,
        "limit": 100
    }
    
    try:
        res = requests.get(url, params=params)
        data = res.json()
        
        if "error" in data:
            return 0
        
        ads = data.get("data", [])
        active_ads = [ad for ad in ads if ad.get("effective_status") == "ACTIVE"]
        
        # インサイトを取得
        low_imp_count = 0
        for ad in active_ads:
            ad_id = ad["id"]
            # 全期間のデータを取得（過去2年間）
            from datetime import datetime, timedelta
            import json as json_lib
            since = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
            until = datetime.now().strftime("%Y-%m-%d")
            
            insights_url = f"https://graph.facebook.com/v19.0/{ad_id}/insights"
            insights_params = {
                "fields": "impressions",
                "time_range": json_lib.dumps({"since": since, "until": until}),
                "access_token": ACCESS_TOKEN
            }
            
            try:
                insights_res = requests.get(insights_url, params=insights_params)
                insights_data = insights_res.json()
                
                if "data" in insights_data and len(insights_data["data"]) > 0:
                    impressions = int(insights_data["data"][0].get("impressions", 0))
                    if impressions <= 500:
                        low_imp_count += 1
            except:
                pass
        
        return low_imp_count
    
    except Exception as e:
        return 0

def send_approval_request(campaign_name, adset_id, adset_name, low_imp_count, total_ads):
    """Slackに承認リクエストを送信"""
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        print("⚠️  Slack通知をスキップ（トークンまたはチャンネルIDが未設定）")
        return None
    
    try:
        from slack_sdk import WebClient
        client = WebClient(token=SLACK_BOT_TOKEN)
        
        # Block Kitメッセージを作成
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔄 広告コピー承認リクエスト"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*キャンペーン:*\n{campaign_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*広告セット:*\n{adset_name}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*広告セットID:*\n`{adset_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*インプレッション500以下:*\n{low_imp_count}件 / {total_ads}件"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "👍 *このメッセージに絵文字でリアクション:*\n✅ = コピーを承認 | ❌ = 却下"
                }
            }
        ]
        
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            blocks=blocks,
            text=f"広告コピー承認リクエスト: {adset_name}"
        )
        
        message_ts = response['ts']
        print(f"✅ Slack承認リクエスト送信成功: {message_ts}")
        
        return message_ts
    
    except Exception as e:
        print(f"❌ Slack承認リクエスト送信エラー: {e}")
        return None

def save_approval_data(approvals):
    """承認データを保存"""
    try:
        with open(APPROVAL_FILE, "w", encoding="utf-8") as f:
            json.dump(approvals, f, ensure_ascii=False, indent=2)
        print(f"✅ 承認データを保存: {APPROVAL_FILE}")
    except Exception as e:
        print(f"❌ 承認データ保存エラー: {e}")

def main():
    """メイン処理"""
    print("=" * 60)
    print("Slack承認フロー付き広告コピー")
    print("=" * 60)
    
    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKENが設定されていません")
        sys.exit(1)
    
    if not CAMPAIGN_IDS or CAMPAIGN_IDS == [""]:
        print("❌ CAMPAIGN_IDSが設定されていません")
        sys.exit(1)
    
    approvals = []
    
    # コピー履歴を読み込み
    copy_history = load_copy_history()
    print(f"\n📋 コピー履歴: {len(copy_history)}件")
    
    # 各キャンペーンを処理
    for campaign_id in CAMPAIGN_IDS:
        campaign_id = campaign_id.strip()
        if not campaign_id:
            continue
        
        # キャンペーン情報を取得
        campaign_info = fetch_campaign_info(campaign_id)
        if not campaign_info:
            print(f"\n❌ キャンペーン {campaign_id} の情報取得に失敗")
            continue
        
        campaign_name = campaign_info.get("name", "不明")
        print(f"\n📣 キャンペーン: {campaign_name}")
        print(f"   ID: {campaign_id}")
        
        # 広告セットを取得
        adsets = fetch_adsets_from_campaign(campaign_id)
        print(f"   広告セット数: {len(adsets)}")
        
        # 各広告セットの承認リクエストを送信
        for adset in adsets:
            adset_id = adset["id"]
            adset_name = adset["name"]
            adset_status = adset.get("effective_status", "不明")
            
            print(f"\n  🎯 広告セット: {adset_name}")
            print(f"     ID: {adset_id}")
            print(f"     ステータス: {adset_status}")
            
            # インプレッション500以下の広告数をカウント
            print(f"     インプレッション500以下の広告を確認中...")
            low_imp_count = count_low_impression_ads(adset_id)
            
            # 広告総数を取得（簡易版）
            total_ads_url = f"https://graph.facebook.com/v19.0/{adset_id}/ads"
            total_ads_params = {
                "fields": "id",
                "access_token": ACCESS_TOKEN,
                "limit": 100
            }
            total_ads_res = requests.get(total_ads_url, params=total_ads_params)
            total_ads_data = total_ads_res.json()
            total_ads = len(total_ads_data.get("data", []))
            
            print(f"     インプレッション500以下: {low_imp_count}件 / {total_ads}件")
            
            # コピー済みかチェック
            if is_already_copied(adset_id, copy_history):
                print(f"     ⚠️  既にコピー済みのためスキップ")
                continue
            
            if low_imp_count == 0:
                print(f"     ⚠️  インプレッション500以下の広告がないためスキップ")
                continue
            
            if low_imp_count <= 3:
                print(f"     ⚠️  インプレッション500以下の広告が3件以下のためスキップ")
                continue
            
            # Slackに承認リクエストを送信
            message_ts = send_approval_request(
                campaign_name,
                adset_id,
                adset_name,
                low_imp_count,
                total_ads
            )
            
            if message_ts:
                approvals.append({
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "adset_id": adset_id,
                    "adset_name": adset_name,
                    "low_imp_count": low_imp_count,
                    "total_ads": total_ads,
                    "message_ts": message_ts,
                    "status": "pending"
                })
    
    # 承認データを保存
    if approvals:
        save_approval_data(approvals)
        print(f"\n✅ {len(approvals)}件の承認リクエストを送信しました")
        print(f"Slackで✅または❌でリアクションしてください")
    else:
        print(f"\n⚠️  承認リクエストを送信する広告セットがありませんでした")

if __name__ == "__main__":
    main()
