#!/usr/bin/env python3
"""
Slackリアクション読み取りテストスクリプト
"""

from slack_reaction_helper import (
    load_reaction_data,
    check_approval_status,
    get_approved_ads
)

def main():
    print("=" * 50)
    print("Slackリアクション読み取りテスト")
    print("=" * 50)
    print()
    
    # リアクションデータを読み込み
    print("1. リアクションデータの読み込み...")
    reaction_data = load_reaction_data()
    
    if not reaction_data:
        print("   リアクションデータが見つかりません")
        print()
        print("   まず以下を実行してください:")
        print("   1. python3 test_slack_bot.py")
        print("   2. Slackでメッセージにリアクション")
        return
    
    print(f"   {len(reaction_data)}件のメッセージを検出")
    print()
    
    # 各メッセージのリアクションを確認
    print("2. リアクションの確認...")
    print()
    
    for i, entry in enumerate(reaction_data, 1):
        ad_id = entry.get("ad_id")
        message_ts = entry.get("message_ts")
        status = entry.get("status")
        
        print(f"   [{i}] 広告ID: {ad_id}")
        print(f"       メッセージID: {message_ts}")
        print(f"       現在のステータス: {status}")
        
        if status == "pending":
            approval_status = check_approval_status(ad_id)
            
            if approval_status == "approved":
                print(f"       リアクション: ✅ 承認")
            elif approval_status == "rejected":
                print(f"       リアクション: ❌ 却下")
            elif approval_status == "pending":
                print(f"       リアクション: なし")
            else:
                print(f"       リアクション: メッセージが見つかりません")
        else:
            print(f"       リアクション: 処理済み")
        
        print()
    
    # 承認済み広告を取得
    print("3. 承認済み広告の取得...")
    approved_ads = get_approved_ads()
    
    if approved_ads:
        print(f"   {len(approved_ads)}件の承認済み広告があります:")
        for ad in approved_ads:
            print(f"   - {ad.get('ad_id')}")
    else:
        print("   承認済み広告はありません")
    
    print()
    print("=" * 50)
    print()
    print("次のステップ:")
    print("  承認済み広告を停止するには:")
    print("  python3 approved_stopper.py")
    print()

if __name__ == "__main__":
    main()
