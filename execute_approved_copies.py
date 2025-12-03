#!/usr/bin/env python3
"""
承認済み広告セットをコピーするスクリプト

Slackで承認された広告セットのみをコピーする
"""

import os
import sys
import json
import subprocess
from dotenv import load_dotenv
from slack_reaction_helper import get_message_reactions

# 環境変数を読み込み
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
APPROVAL_FILE = "ad_copy_approvals.json"

def load_approval_data():
    """承認データを読み込み"""
    if not os.path.exists(APPROVAL_FILE):
        print(f"⚠️  承認データファイルが見つかりません: {APPROVAL_FILE}")
        return []
    
    try:
        with open(APPROVAL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ 承認データを読み込み: {len(data)}件")
        return data
    except Exception as e:
        print(f"❌ 承認データ読み込みエラー: {e}")
        return []

def save_approval_data(approvals):
    """承認データを保存"""
    try:
        with open(APPROVAL_FILE, "w", encoding="utf-8") as f:
            json.dump(approvals, f, ensure_ascii=False, indent=2)
        print(f"✅ 承認データを保存: {APPROVAL_FILE}")
    except Exception as e:
        print(f"❌ 承認データ保存エラー: {e}")

def check_approval_status(message_ts):
    """Slackリアクションで承認状態を確認"""
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        return None
    
    reactions = get_message_reactions(SLACK_CHANNEL_ID, message_ts)
    
    if not reactions:
        return "pending"
    
    # ✅があれば承認
    if "white_check_mark" in reactions:
        return "approved"
    
    # ❌があれば却下
    if "x" in reactions:
        return "rejected"
    
    return "pending"

def main():
    """メイン処理"""
    print("=" * 60)
    print("承認済み広告セットのコピー実行")
    print("=" * 60)
    
    # 承認データを読み込み
    approvals = load_approval_data()
    
    if not approvals:
        print("⚠️  処理する承認データがありません")
        sys.exit(0)
    
    # 統計情報
    approved_count = 0
    rejected_count = 0
    pending_count = 0
    success_count = 0
    error_count = 0
    
    # 各承認リクエストを処理
    for approval in approvals:
        adset_id = approval["adset_id"]
        adset_name = approval["adset_name"]
        message_ts = approval["message_ts"]
        current_status = approval.get("status", "pending")
        
        print(f"\n🎯 広告セット: {adset_name}")
        print(f"   ID: {adset_id}")
        print(f"   現在のステータス: {current_status}")
        
        # 既に処理済みの場合はスキップ
        if current_status in ["approved_executed", "rejected"]:
            print(f"   ⚠️  既に処理済みのためスキップ")
            continue
        
        # Slackリアクションを確認
        status = check_approval_status(message_ts)
        print(f"   Slackリアクション: {status}")
        
        if status == "approved":
            approved_count += 1
            print(f"   ✅ 承認されました - コピーを実行します")
            
            # ad_copy_low_impression.pyを実行
            env = os.environ.copy()
            env["TARGET_ADSET_ID"] = adset_id
            
            try:
                result = subprocess.run(
                    ["python3", "ad_copy_low_impression.py"],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    print(f"   ✅ コピー成功")
                    approval["status"] = "approved_executed"
                    success_count += 1
                else:
                    print(f"   ❌ コピー失敗")
                    print(f"   出力: {result.stdout}")
                    approval["status"] = "approved_error"
                    error_count += 1
            
            except subprocess.TimeoutExpired:
                print(f"   ❌ タイムアウト")
                approval["status"] = "approved_error"
                error_count += 1
            except Exception as e:
                print(f"   ❌ エラー: {e}")
                approval["status"] = "approved_error"
                error_count += 1
        
        elif status == "rejected":
            rejected_count += 1
            print(f"   ❌ 却下されました")
            approval["status"] = "rejected"
        
        else:
            pending_count += 1
            print(f"   ⏳ まだ承認されていません")
    
    # 承認データを保存
    save_approval_data(approvals)
    
    # サマリーを表示
    print("\n" + "=" * 60)
    print("処理完了")
    print("=" * 60)
    print(f"承認済み: {approved_count}")
    print(f"却下: {rejected_count}")
    print(f"保留中: {pending_count}")
    print(f"コピー成功: {success_count}")
    print(f"コピー失敗: {error_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
