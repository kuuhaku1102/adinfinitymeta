#!/usr/bin/env python3
"""
元の広告セットとV2広告セットのパフォーマンスを比較するスクリプト
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


def fetch_adset_insights(adset_id, days=7):
    """広告セットのインサイトを取得"""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    until = datetime.now().strftime("%Y-%m-%d")
    
    url = f"https://graph.facebook.com/v21.0/{adset_id}/insights"
    params = {
        "access_token": ACCESS_TOKEN,
        "time_range": json.dumps({"since": since, "until": until}),
        "fields": "impressions,spend,clicks,ctr,cpc,actions"
    }
    
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json().get("data", [])
            return data[0] if data else {}
        else:
            print(f"⚠️  広告セットインサイト取得失敗 (ID: {adset_id}): {res.status_code}")
            return {}
    except Exception as e:
        print(f"❌ 広告セットインサイト取得エラー (ID: {adset_id}): {e}")
        return {}


def calculate_cpa(insights):
    """CPAを計算"""
    spend = float(insights.get("spend", 0))
    actions = insights.get("actions", [])
    
    conversions = 0
    for action in actions:
        action_type = action.get("action_type", "")
        if action_type in ["lead", "onsite_conversion.lead_grouped"]:
            conversions += int(action.get("value", 0))
    
    if conversions > 0:
        return spend / conversions
    return None


def send_slack_notification(blocks, text):
    """Slackに通知を送信（Block Kit対応）"""
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
        "blocks": blocks,
        "text": text
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200 and res.json().get("ok"):
            print("✅ Slack通知送信成功")
        else:
            print(f"❌ Slack通知送信失敗: {res.text}")
    except Exception as e:
        print(f"❌ Slack通知送信エラー: {e}")


def compare_adsets(original_adset_id, v2_adset_id, original_name, v2_name, days=7):
    """2つの広告セットのパフォーマンスを比較"""
    print(f"\n{'='*60}")
    print(f"パフォーマンス比較: {original_name} vs {v2_name}")
    print(f"{'='*60}\n")
    
    # インサイトを取得
    print("元の広告セットのインサイトを取得中...")
    original_insights = fetch_adset_insights(original_adset_id, days)
    
    print("V2広告セットのインサイトを取得中...")
    v2_insights = fetch_adset_insights(v2_adset_id, days)
    
    # メトリクスを抽出
    original_impressions = int(original_insights.get("impressions", 0))
    v2_impressions = int(v2_insights.get("impressions", 0))
    
    original_spend = float(original_insights.get("spend", 0))
    v2_spend = float(v2_insights.get("spend", 0))
    
    original_clicks = int(original_insights.get("clicks", 0))
    v2_clicks = int(v2_insights.get("clicks", 0))
    
    original_ctr = float(original_insights.get("ctr", 0))
    v2_ctr = float(v2_insights.get("ctr", 0))
    
    original_cpa = calculate_cpa(original_insights)
    v2_cpa = calculate_cpa(v2_insights)
    
    # 結果を表示
    print("\n【元の広告セット】")
    print(f"  インプレッション: {original_impressions:,}")
    print(f"  支出: ¥{original_spend:,.0f}")
    print(f"  クリック: {original_clicks:,}")
    print(f"  CTR: {original_ctr:.2f}%")
    print(f"  CPA: ¥{original_cpa:,.0f}" if original_cpa else "  CPA: N/A")
    
    print("\n【V2広告セット】")
    print(f"  インプレッション: {v2_impressions:,}")
    print(f"  支出: ¥{v2_spend:,.0f}")
    print(f"  クリック: {v2_clicks:,}")
    print(f"  CTR: {v2_ctr:.2f}%")
    print(f"  CPA: ¥{v2_cpa:,.0f}" if v2_cpa else "  CPA: N/A")
    
    # 優勝者を判定
    winner = None
    if original_cpa and v2_cpa:
        if v2_cpa < original_cpa:
            winner = "V2"
            improvement = ((original_cpa - v2_cpa) / original_cpa) * 100
        else:
            winner = "元"
            improvement = ((v2_cpa - original_cpa) / v2_cpa) * 100
    
    # Slack通知を作成
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📊 広告セットパフォーマンス比較 ({days}日間)*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*元の広告セット:*\n{original_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*V2広告セット:*\n{v2_name}"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*インプレッション:*\n元: {original_impressions:,}\nV2: {v2_impressions:,}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*支出:*\n元: ¥{original_spend:,.0f}\nV2: ¥{v2_spend:,.0f}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*クリック:*\n元: {original_clicks:,}\nV2: {v2_clicks:,}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*CTR:*\n元: {original_ctr:.2f}%\nV2: {v2_ctr:.2f}%"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*CPA:*\n元: {'¥{:,.0f}'.format(original_cpa) if original_cpa else 'N/A'}\nV2: {'¥{:,.0f}'.format(v2_cpa) if v2_cpa else 'N/A'}"
                }
            ]
        }
    ]
    
    if winner:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🏆 優勝者: {winner}の広告セット*\nCPA改善率: {improvement:.1f}%"
            }
        })
    
    fallback_text = f"📊 広告セットパフォーマンス比較\n\n元: {original_name}\nV2: {v2_name}\n\n優勝者: {winner}の広告セット" if winner else f"📊 広告セットパフォーマンス比較\n\n元: {original_name}\nV2: {v2_name}"
    
    send_slack_notification(blocks, fallback_text)
    
    print(f"\n{'='*60}")
    print("比較完了")
    print(f"{'='*60}\n")


def main():
    """メイン処理"""
    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKENが未設定です")
        return
    
    # コピー履歴を読み込み
    history = load_copy_history()
    
    if not history:
        print("⚠️  コピー履歴が見つかりません")
        return
    
    # 最新のコピー履歴を取得
    latest = history[-1]
    
    # 作成日時をチェック
    created_at = datetime.fromisoformat(latest["timestamp"])
    days_since_creation = (datetime.now() - created_at).days
    
    print(f"最新のコピー: {latest['original_adset_name']}")
    print(f"作成日時: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"経過日数: {days_since_creation}日")
    
    if days_since_creation < 7:
        print(f"\n⚠️  まだ7日経過していません（{days_since_creation}日経過）")
        print("7日後に再度実行してください")
        return
    
    # パフォーマンス比較
    compare_adsets(
        latest["original_adset_id"],
        latest["v2_adset_id"],
        latest["original_adset_name"],
        latest["v2_adset_name"],
        days=7
    )


if __name__ == "__main__":
    main()
