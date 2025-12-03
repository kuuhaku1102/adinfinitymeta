#!/usr/bin/env python3
"""
Slack Bot接続テストスクリプト
"""

from slack_reaction_helper import test_slack_connection, send_slack_message_with_bot

def main():
    print("=" * 50)
    print("Slack Bot 接続テスト")
    print("=" * 50)
    print()
    
    # 接続テスト
    print("1. Slack Bot Token の確認...")
    if not test_slack_connection():
        print()
        print("❌ 接続に失敗しました")
        print()
        print("確認事項:")
        print("  1. .envファイルにSLACK_BOT_TOKENが設定されているか")
        print("  2. Bot Tokenが正しいか（xoxb-で始まる）")
        print("  3. Botがワークスペースにインストールされているか")
        return
    
    print()
    print("2. テストメッセージの送信...")
    
    test_message = """🧪 *テストメッセージ*

これはSlack Bot接続のテストメッセージです。

👍 このメッセージに絵文字でリアクション:
  ✅ = テスト成功
  ❌ = テスト失敗
"""
    
    message_ts = send_slack_message_with_bot(test_message, "test_ad_id")
    
    if message_ts:
        print()
        print("✅ テストメッセージの送信に成功しました！")
        print(f"   メッセージID: {message_ts}")
        print()
        print("次のステップ:")
        print("  1. Slackチャンネルでテストメッセージを確認")
        print("  2. メッセージに✅または❌でリアクション")
        print("  3. python3 test_slack_reactions.py でリアクションを確認")
    else:
        print()
        print("❌ テストメッセージの送信に失敗しました")
        print()
        print("確認事項:")
        print("  1. .envファイルにSLACK_CHANNEL_IDが設定されているか")
        print("  2. チャンネルIDが正しいか")
        print("  3. Botがチャンネルに追加されているか (/invite @Bot名)")
    
    print()
    print("=" * 50)

if __name__ == "__main__":
    main()
