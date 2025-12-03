#!/usr/bin/env python3
"""
全広告セット自動処理スクリプト

指定したキャンペーン内の全広告セットを自動的に取得し、
インプレッション500以下の広告をコピーする
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
CAMPAIGN_IDS = os.getenv("CAMPAIGN_IDS", "").split(",")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

def check_token_permissions():
    """アクセストークンの権限を確認"""
    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKENが設定されていません")
        return False
    
    print("\n" + "="*60)
    print("🔍 アクセストークンの権限を確認中...")
    print("="*60)
    
    url = "https://graph.facebook.com/v21.0/debug_token"
    params = {
        "input_token": ACCESS_TOKEN,
        "access_token": ACCESS_TOKEN
    }
    
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json()
            token_data = data.get("data", {})
            
            scopes = token_data.get("scopes", [])
            print(f"権限一覧 ({len(scopes)}個):")
            for scope in sorted(scopes):
                print(f"  ✓ {scope}")
            
            # 必要な権限をチェック
            required_permissions = ["ads_management", "ads_read"]
            missing_permissions = []
            
            for perm in required_permissions:
                if perm in scopes:
                    print(f"  ✅ {perm}: あり")
                else:
                    print(f"  ❌ {perm}: なし")
                    missing_permissions.append(perm)
            
            print("="*60 + "\n")
            
            if missing_permissions:
                print(f"❌ 以下の権限が不足しています: {', '.join(missing_permissions)}")
                return False
            
            return True
        else:
            print(f"❌ トークン情報取得失敗: {res.status_code}")
            print(f"レスポンス: {res.text}")
            return False
    
    except Exception as e:
        print(f"❌ エラー: {e}")
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
            print(f"❌ キャンペーン情報取得エラー: {data['error']['message']}")
            return None
        
        return data
    
    except Exception as e:
        print(f"❌ キャンペーン情報取得エラー: {e}")
        return None

def fetch_adsets_from_campaign(campaign_id):
    """キャンペーンから全広告セットを取得"""
    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKENが設定されていません")
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
            print(f"❌ キャンペーン {campaign_id} の広告セット取得エラー: {data['error']['message']}")
            return []
        
        adsets = data.get("data", [])
        print(f"✅ キャンペーン {campaign_id} から {len(adsets)} 件の広告セットを取得")
        
        # ACTIVEな広告セットのみをフィルタ
        active_adsets = [ad for ad in adsets if ad.get("effective_status") == "ACTIVE"]
        print(f"   └ ACTIVE: {len(active_adsets)} 件")
        
        return active_adsets
    
    except Exception as e:
        print(f"❌ キャンペーン {campaign_id} の広告セット取得エラー: {e}")
        return []

def send_slack_summary(total_adsets, processed_adsets, skipped_adsets, errors):
    """Slackに処理結果のサマリーを送信"""
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        print("⚠️  Slack通知をスキップ（トークンまたはチャンネルIDが未設定）")
        return
    
    try:
        from slack_sdk import WebClient
        client = WebClient(token=SLACK_BOT_TOKEN)
        
        # サマリーメッセージを作成
        summary_text = f"""
📊 *全広告セット処理完了*

*処理結果:*
• 対象広告セット数: {total_adsets}
• 処理成功: {processed_adsets}
• スキップ: {skipped_adsets}
• エラー: {errors}
"""
        
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text=summary_text
        )
        
        print(f"✅ Slackサマリー送信成功: {response['ts']}")
    
    except Exception as e:
        print(f"❌ Slackサマリー送信エラー: {e}")

def main():
    """メイン処理"""
    print("=" * 60)
    print("全広告セット自動処理を開始")
    print("=" * 60)
    
    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKENが設定されていません")
        sys.exit(1)
    
    if not CAMPAIGN_IDS or CAMPAIGN_IDS == [""]:
        print("❌ CAMPAIGN_IDSが設定されていません")
        sys.exit(1)
    
    # 権限を確認
    if not check_token_permissions():
        print("❌ アクセストークンの権限が不足しています")
        sys.exit(1)
    
    # 統計情報
    total_adsets = 0
    processed_adsets = 0
    skipped_adsets = 0
    errors = 0
    
    # 各キャンペーンを処理
    for campaign_id in CAMPAIGN_IDS:
        campaign_id = campaign_id.strip()
        if not campaign_id:
            continue
        
        # キャンペーン情報を取得
        campaign_info = fetch_campaign_info(campaign_id)
        if campaign_info:
            campaign_name = campaign_info.get("name", "不明")
            campaign_status = campaign_info.get("effective_status", "不明")
            print(f"\n📣 キャンペーン: {campaign_name}")
            print(f"   ID: {campaign_id}")
            print(f"   ステータス: {campaign_status}")
        else:
            print(f"\n📣 キャンペーン {campaign_id} を処理中...")
        
        # 広告セットを取得
        adsets = fetch_adsets_from_campaign(campaign_id)
        total_adsets += len(adsets)
        
        # 各広告セットを処理
        for adset in adsets:
            adset_id = adset["id"]
            adset_name = adset["name"]
            
            print(f"\n  🎯 広告セット: {adset_name} (ID: {adset_id})")
            
            # ad_copy_low_impression.pyを呼び出し
            import subprocess
            env = os.environ.copy()
            env["TARGET_ADSET_ID"] = adset_id
            
            try:
                result = subprocess.run(
                    ["python3", "ad_copy_low_impression.py"],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分タイムアウト
                )
                
                # 詳細出力を常に表示
                print("\n" + "="*50)
                print("[詳細出力]")
                print("="*50)
                print(result.stdout)
                if result.stderr:
                    print("\n[エラー出力]")
                    print(result.stderr)
                print("="*50 + "\n")
                
                if result.returncode == 0:
                    print(f"  ✅ 処理成功")
                    processed_adsets += 1
                else:
                    print(f"  ⚠️  スキップまたはエラー")
                    if "スキップ" in result.stdout:
                        skipped_adsets += 1
                    else:
                        errors += 1
                
            except subprocess.TimeoutExpired:
                print(f"  ❌ タイムアウト（5分以上）")
                errors += 1
            except Exception as e:
                print(f"  ❌ エラー: {e}")
                errors += 1
    
    # サマリーを表示
    print("\n" + "=" * 60)
    print("処理完了")
    print("=" * 60)
    print(f"対象広告セット数: {total_adsets}")
    print(f"処理成功: {processed_adsets}")
    print(f"スキップ: {skipped_adsets}")
    print(f"エラー: {errors}")
    print("=" * 60)
    
    # Slackに通知
    send_slack_summary(total_adsets, processed_adsets, skipped_adsets, errors)

if __name__ == "__main__":
    main()
