import os
import json
import requests
from datetime import datetime

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        print("[警告] python-dotenvが未インストールのため、.env読み込みをスキップします")
        return False

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
REACTION_DATA_FILE = "slack_reactions.json"

# リアクションの絵文字
APPROVE_EMOJI = "white_check_mark"  # ✅
REJECT_EMOJI = "x"  # ❌

def load_reaction_data():
    """リアクションデータを読み込む"""
    if not os.path.exists(REACTION_DATA_FILE):
        return []
    try:
        with open(REACTION_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"リアクションデータ読み込みエラー: {e}")
        return []

def save_reaction_data(data):
    """リアクションデータを保存する"""
    try:
        with open(REACTION_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"リアクションデータ保存エラー: {e}")
        return False

def send_slack_message_with_bot(text, ad_id):
    """
    Slack Bot Tokenを使ってメッセージを送信し、メッセージIDを記録
    """
    if not SLACK_BOT_TOKEN:
        print("[警告] SLACK_BOT_TOKENが未設定です")
        return None
    
    if not SLACK_CHANNEL_ID:
        print("[警告] SLACK_CHANNEL_IDが未設定です")
        return None
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": SLACK_CHANNEL_ID,
        "text": text
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        result = res.json()
        
        if result.get("ok"):
            message_ts = result.get("ts")
            print(f"✅ Slackメッセージ送信成功: {message_ts}")
            
            # メッセージIDと広告IDを記録
            reaction_data = load_reaction_data()
            reaction_data.append({
                "ad_id": ad_id,
                "message_ts": message_ts,
                "channel_id": SLACK_CHANNEL_ID,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            })
            save_reaction_data(reaction_data)
            
            return message_ts
        else:
            error_msg = result.get('error')
            error_detail = result.get('response_metadata', {})
            print(f"❌ Slackメッセージ送信失敗: {error_msg}")
            if error_detail:
                print(f"   詳細: {error_detail}")
            return None
    except Exception as e:
        print(f"❌ Slackメッセージ送信エラー: {e}")
        return None

def send_slack_message_with_blocks(blocks, text, ad_id, ad_name=""):
    """
    Slack Block Kitを使ってリッチなメッセージを送信
    """
    if not SLACK_BOT_TOKEN:
        print("[警告] SLACK_BOT_TOKENが未設定です")
        return None
    
    if not SLACK_CHANNEL_ID:
        print("[警告] SLACK_CHANNEL_IDが未設定です")
        return None
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": SLACK_CHANNEL_ID,
        "blocks": blocks,
        "text": text  # フォールバック用
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        result = res.json()
        
        if result.get("ok"):
            message_ts = result.get("ts")
            print(f"✅ Slackメッセージ送信成功: {message_ts}")
            
            # メッセージIDと広告IDを記録
            reaction_data = load_reaction_data()
            reaction_data.append({
                "ad_id": ad_id,
                "ad_name": ad_name,
                "message_ts": message_ts,
                "channel_id": SLACK_CHANNEL_ID,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            })
            save_reaction_data(reaction_data)
            
            return message_ts
        else:
            error_msg = result.get('error')
            error_detail = result.get('response_metadata', {})
            print(f"❌ Slackメッセージ送信失敗: {error_msg}")
            if error_detail:
                print(f"   詳細: {error_detail}")
            return None
    except Exception as e:
        print(f"❌ Slackメッセージ送信エラー: {e}")
        return None

def get_message_reactions(message_ts):
    """
    メッセージのリアクションを取得
    """
    if not SLACK_BOT_TOKEN:
        print("[警告] SLACK_BOT_TOKENが未設定です")
        return []
    
    if not SLACK_CHANNEL_ID:
        print("[警告] SLACK_CHANNEL_IDが未設定です")
        return []
    
    url = "https://slack.com/api/reactions.get"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    params = {
        "channel": SLACK_CHANNEL_ID,
        "timestamp": message_ts
    }
    
    try:
        res = requests.get(url, headers=headers, params=params)
        result = res.json()
        
        if result.get("ok"):
            reactions = result.get("message", {}).get("reactions", [])
            return reactions
        else:
            error = result.get("error")
            if error != "message_not_found":
                print(f"リアクション取得エラー: {error}")
            return []
    except Exception as e:
        print(f"リアクション取得エラー: {e}")
        return []

def check_approval_status(ad_id):
    """
    広告IDに対する承認状態をチェック
    
    Returns:
        "approved": ✅リアクションあり
        "rejected": ❌リアクションあり
        "pending": リアクションなし
        None: メッセージが見つからない
    """
    reaction_data = load_reaction_data()
    
    # 広告IDに対応するメッセージを検索
    message_entry = None
    for entry in reaction_data:
        if entry.get("ad_id") == ad_id and entry.get("status") == "pending":
            message_entry = entry
            break
    
    if not message_entry:
        return None
    
    message_ts = message_entry.get("message_ts")
    reactions = get_message_reactions(message_ts)
    
    # リアクションをチェック
    has_approve = False
    has_reject = False
    
    for reaction in reactions:
        emoji = reaction.get("name")
        if emoji == APPROVE_EMOJI:
            has_approve = True
        elif emoji == REJECT_EMOJI:
            has_reject = True
    
    # 承認が優先
    if has_approve:
        return "approved"
    elif has_reject:
        return "rejected"
    else:
        return "pending"

def get_approved_ads():
    """
    ✅リアクションがついた広告のリストを取得
    """
    reaction_data = load_reaction_data()
    approved_ads = []
    
    for entry in reaction_data:
        if entry.get("status") != "pending":
            continue
        
        ad_id = entry.get("ad_id")
        status = check_approval_status(ad_id)
        
        if status == "approved":
            approved_ads.append({
                "ad_id": ad_id,
                "message_ts": entry.get("message_ts"),
                "created_at": entry.get("created_at")
            })
            
            # ステータスを更新
            entry["status"] = "approved"
            entry["approved_at"] = datetime.now().isoformat()
    
    # 更新を保存
    save_reaction_data(reaction_data)
    
    print(f"✅ 承認済み広告: {len(approved_ads)}件")
    return approved_ads

def mark_as_stopped(ad_id):
    """
    広告を停止済みとしてマーク
    """
    reaction_data = load_reaction_data()
    
    for entry in reaction_data:
        if entry.get("ad_id") == ad_id:
            entry["status"] = "stopped"
            entry["stopped_at"] = datetime.now().isoformat()
            save_reaction_data(reaction_data)
            print(f"✅ 広告 {ad_id} を停止済みにマークしました")
            return True
    
    return False

def test_slack_connection():
    """
    Slack接続のテスト
    """
    if not SLACK_BOT_TOKEN:
        print("❌ SLACK_BOT_TOKENが未設定です")
        return False
    
    if not SLACK_CHANNEL_ID:
        print("❌ SLACK_CHANNEL_IDが未設定です")
        return False
    
    url = "https://slack.com/api/auth.test"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    
    try:
        res = requests.get(url, headers=headers)
        result = res.json()
        
        if result.get("ok"):
            print(f"✅ Slack接続成功")
            print(f"   Bot名: {result.get('user')}")
            print(f"   チーム: {result.get('team')}")
            return True
        else:
            print(f"❌ Slack接続失敗: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Slack接続エラー: {e}")
        return False

if __name__ == "__main__":
    # テスト実行
    print("=== Slack Bot 接続テスト ===")
    test_slack_connection()
