#!/usr/bin/env python3
"""
Slack Block Kit メッセージのテストスクリプト
"""

from slack_reaction_helper import send_slack_message_with_blocks

def main():
    print("=" * 50)
    print("Slack Block Kit メッセージテスト")
    print("=" * 50)
    print()
    
    # テスト用のブロック
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📣 Meta広告通知 [STOP候補]*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*キャンペーン名:*\n春キャンペーン2025"
                },
                {
                    "type": "mrkdwn",
                    "text": "*広告セット名:*\n東京ターゲット"
                },
                {
                    "type": "mrkdwn",
                    "text": "*広告名:*\nテスト広告A"
                },
                {
                    "type": "mrkdwn",
                    "text": "*CPA:*\n¥1,500"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*広告ID:* `test_ad_12345`"
            }
        },
        {
            "type": "image",
            "image_url": "https://picsum.photos/800/400",
            "alt_text": "広告画像: テスト広告A"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "👍 このメッセージに絵文字でリアクション: ✅ = 停止を承認 | ❌ = 却下"
                }
            ]
        }
    ]
    
    fallback_text = "📣 Meta広告通知 [STOP候補]\n\nキャンペーン: 春キャンペーン2025\n広告セット: 東京ターゲット\n広告名: テスト広告A\nCPA: ¥1,500\n広告ID: test_ad_12345"
    
    print("Block Kitメッセージを送信中...")
    message_ts = send_slack_message_with_blocks(blocks, fallback_text, "test_ad_12345", "テスト広告A")
    
    if message_ts:
        print()
        print("✅ Block Kitメッセージの送信に成功しました！")
        print(f"   メッセージID: {message_ts}")
        print()
        print("Slackチャンネルで以下を確認してください:")
        print("  - キャンペーン名、広告セット名、広告名が表示されている")
        print("  - CPAが表示されている")
        print("  - 広告画像が表示されている")
        print("  - リアクション用の説明が表示されている")
    else:
        print()
        print("❌ Block Kitメッセージの送信に失敗しました")
    
    print()
    print("=" * 50)

if __name__ == "__main__":
    main()
