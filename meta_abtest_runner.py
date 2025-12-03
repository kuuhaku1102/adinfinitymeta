import os
import json
from datetime import datetime

import requests
import gspread
from slack_reaction_helper import send_slack_message_with_bot, send_slack_message_with_blocks

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        """Fallback when python-dotenv is not installed."""
        print("[警告] python-dotenvが未インストールのため、.env読み込みをスキップします")
        return False
from oauth2client.service_account import ServiceAccountCredentials

# 固定設定
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
ACCOUNT_IDS = os.getenv("ACCOUNT_IDS")
CAMPAIGN_IDS = "120231962646350484,120230617419590484"  # ← 固定のキャンペーンID
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")
APPROVAL_WEB_URL = os.getenv("APPROVAL_WEB_URL", "http://localhost:5000")  # 承認用WebページのURL

APPROVAL_FILE = "pending_approvals.json"

if not ACCESS_TOKEN:
    print("[警告] ACCESS_TOKENが未設定のため、Meta APIへのアクセスはスキップされます")

# --- Account IDの取得 ---
def get_account_ids():
    if ACCOUNT_IDS:
        return [aid.strip() for aid in ACCOUNT_IDS.split(',') if aid.strip()]
    elif ACCOUNT_ID:
        return [ACCOUNT_ID]
    else:
        print("[警告] ACCOUNT_IDまたはACCOUNT_IDSが未設定です")
        return []

# --- Campaign IDの取得 ---
def get_campaign_ids():
    if CAMPAIGN_IDS:
        return [cid.strip() for cid in CAMPAIGN_IDS.split(',') if cid.strip()]
    return []

# --- JSON Approval Management ---
def load_approvals():
    """承認データを読み込む"""
    if not os.path.exists(APPROVAL_FILE):
        return []
    try:
        with open(APPROVAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"承認データ読み込みエラー: {e}")
        return []

def save_approvals(data):
    """承認データを保存する"""
    try:
        with open(APPROVAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"承認データ保存エラー: {e}")
        return False

def add_pending_approval(ad_id, ad_name, campaign_name, adset_name, cpa, image_url):
    """停止候補を承認待ちリストに追加"""
    approvals = load_approvals()
    
    # 既に同じ広告IDが存在するかチェック
    existing = next((a for a in approvals if a.get('ad_id') == ad_id), None)
    if existing and existing.get('status') == 'pending':
        print(f"ℹ️ 広告 {ad_id} は既に承認待ちリストに存在します")
        return False
    
    new_approval = {
        "ad_id": ad_id,
        "ad_name": ad_name,
        "campaign_name": campaign_name,
        "adset_name": adset_name,
        "cpa": cpa,
        "image_url": image_url,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "approved_at": None,
        "approved_by": None
    }
    
    approvals.append(new_approval)
    save_approvals(approvals)
    print(f"✅ 広告 {ad_id} を承認待ちリストに追加しました")
    return True

# --- Google Sheets ---
def get_sheet():
    if not SPREADSHEET_URL:
        print("[警告] SPREADSHEET_URLが未設定のため、スプレッドシートへの書き込みをスキップします")
        return None

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SPREADSHEET_URL).sheet1
        return sheet
    except Exception as e:
        print("[警告] スプレッドシートへの接続に失敗しました:", e)
        return None

def write_rows_to_sheet(rows):
    sheet = get_sheet()
    if not sheet:
        return

    if not sheet.row_values(1):
        sheet.append_row(["広告キャンペーン", "広告グループ", "広告ID", "広告名", "CPA", "画像URL"])
    sheet.append_rows(rows, value_input_option='USER_ENTERED')

# --- Meta API Fetch Functions ---
def fetch_ad_ids(account_id, campaign_ids=None):
    if not ACCESS_TOKEN:
        return []

    ads = []
    if campaign_ids and len(campaign_ids) > 0:
        for cid in campaign_ids:
            url = f"https://graph.facebook.com/v19.0/{cid}/ads"
            params = [
                ("fields", "id,name,effective_status"),
                ("limit", 50),
                ("access_token", ACCESS_TOKEN),
                ("effective_status", "['ACTIVE']")  # 元のまま使用
            ]
            res = requests.get(url, params=params)
            print(f"キャンペーン {cid} の広告取得ステータス:", res.status_code)
            print("レスポンス内容:", res.text)  # ← ここで詳細確認
            if res.status_code == 200:
                ads.extend(res.json().get("data", []))
        return ads
    else:
        print(f"[スキップ] campaign_ids が空または未指定のため、アカウント {account_id} の広告取得をスキップ")
        return []

def fetch_ad_insights(ad_id, date_preset="last_14d"):
    if not ACCESS_TOKEN:
        return {}

    url = f"https://graph.facebook.com/v19.0/{ad_id}/insights"
    params = {
        "fields": "impressions,clicks,spend,actions,cost_per_action_type",
        "date_preset": date_preset,
        "access_token": ACCESS_TOKEN
    }
    res = requests.get(url, params=params)
    print(f"📊 Insights for {ad_id} ({date_preset}):", res.text)
    return res.json().get("data", [])[0] if res.json().get("data") else {}

def fetch_lifetime_insights(ad_id):
    """全期間のインサイトを取得（過去2年間）"""
    if not ACCESS_TOKEN:
        return {}
    
    # 過去2年間のデータを取得（lifetimeの代わり）
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2年間
    
    url = f"https://graph.facebook.com/v19.0/{ad_id}/insights"
    params = {
        "fields": "impressions,clicks,spend,actions,cost_per_action_type",
        "time_range": f'{{"since":"{start_date.strftime("%Y-%m-%d")}","until":"{end_date.strftime("%Y-%m-%d")}"}}',
        "access_token": ACCESS_TOKEN
    }
    
    try:
        res = requests.get(url, params=params)
        print(f"📊 Lifetime Insights for {ad_id}:", res.text[:200])  # 最初の200文字だけ表示
        data = res.json().get("data", [])
        return data[0] if data else {}
    except Exception as e:
        print(f"❌ 全期間インサイト取得エラー ({ad_id}): {e}")
        return {}

def has_lifetime_conversions(ad_id):
    """全期間でコンバージョンがあるかチェック"""
    insights = fetch_lifetime_insights(ad_id)
    try:
        conversions = next(
            (int(a['value']) for a in insights.get("actions", [])
             if a["action_type"] in ["lead", "onsite_conversion.lead_grouped"]),
            0
        )
        has_cv = conversions > 0
        print(f"✅ 広告 {ad_id} の全期間CV: {conversions} (保護: {has_cv})")
        return has_cv
    except Exception as e:
        print(f"❌ 全期間CV確認エラー ({ad_id}):", e)
        return False

def fetch_creative_image_url(ad_id):
    if not ACCESS_TOKEN:
        return "画像なし"

    url = f"https://graph.facebook.com/v19.0/{ad_id}?fields=creative{{thumbnail_url}}&access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    return res.json().get("creative", {}).get("thumbnail_url", "画像なし")

def fetch_ad_details(ad_id):
    if not ACCESS_TOKEN:
        return {}

    url = f"https://graph.facebook.com/v19.0/{ad_id}"
    params = {"fields": "name,campaign_id,adset_id", "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    return res.json()

def fetch_campaign_name(campaign_id):
    if not ACCESS_TOKEN:
        return "不明なキャンペーン"

    url = f"https://graph.facebook.com/v19.0/{campaign_id}"
    params = {"fields": "name", "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    return res.json().get("name", "不明なキャンペーン")

def fetch_adset_name(adset_id):
    if not ACCESS_TOKEN:
        return "不明な広告セット"

    url = f"https://graph.facebook.com/v19.0/{adset_id}"
    params = {"fields": "name", "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    return res.json().get("name", "不明な広告セット")

# --- Metrics Calculation ---
def calculate_metrics(ad):
    try:
        insights = ad.get("insights", {})
        conversions = next(
            (int(a['value']) for a in insights.get("actions", [])
             if a["action_type"] in ["lead", "onsite_conversion.lead_grouped"]),
            0
        )
        clicks = int(insights.get("clicks", 0))
        impressions = int(insights.get("impressions", 0))
        spend = float(insights.get("spend", 0))
        cpa = round(spend / conversions, 2) if conversions > 0 else None
        ctr = round(clicks / impressions, 4) if impressions > 0 else 0
        return cpa, ctr
    except Exception as e:
        print("❌ 指標計算エラー:", e)
        return None, 0

def post_slack_message(text):
    if not SLACK_WEBHOOK_URL:
        print("[警告] SLACK_WEBHOOK_URLが未設定です")
        return False

    payload = {"text": text}
    res = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print("Slack通知結果:", res.status_code)
    return res.status_code == 200


def send_slack_notice(ad, cpa, image_url, label):
    if not ACCESS_TOKEN:
        print("[警告] ACCESS_TOKENが未設定のため、広告詳細を取得できず、Slack通知をスキップします")
        return

    ad_id = ad['id']
    ad_name = ad['name']
    ad_details = fetch_ad_details(ad_id)
    campaign_name = fetch_campaign_name(ad_details.get("campaign_id", ""))
    adset_name = fetch_adset_name(ad_details.get("adset_id", ""))

    # Slack Block Kitでリッチなメッセージを作成
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📣 Meta広告通知 [{label}]*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*キャンペーン名:*\n{campaign_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*広告セット名:*\n{adset_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*広告名:*\n{ad_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*CPA:*\n¥{cpa if cpa is not None else 'N/A'}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*広告ID:* `{ad_id}`"
            }
        }
    ]
    
    # 画像があれば追加
    if image_url and image_url != "N/A":
        blocks.append({
            "type": "image",
            "image_url": image_url,
            "alt_text": f"広告画像: {ad_name}"
        })
    
    # リアクションの説明
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "👍 このメッセージに絵文字でリアクション: ✅ = 停止を承認 | ❌ = 却下"
            }
        ]
    })
    
    # フォールバック用のテキスト
    fallback_text = f"📣 Meta広告通知 [{label}]\n\nキャンペーン: {campaign_name}\n広告セット: {adset_name}\n広告名: {ad_name}\nCPA: ¥{cpa if cpa is not None else 'N/A'}\n広告ID: {ad_id}"
    
    # Slack Bot Tokenを使ってメッセージを送信
    message_ts = send_slack_message_with_blocks(blocks, fallback_text, ad_id, ad_name)
    
    if not message_ts:
        # Bot Tokenが使えない場合はWebhookで送信
        print("⚠️  Bot Tokenが使えないため、Webhookで送信します")
        post_slack_message(fallback_text)


def notify_no_stop_candidates(account_id, reason=None):
    message = ["*📣 Meta広告通知 [停止対象なし]*", "", f"*アカウントID*: {account_id}", "指定された条件で停止対象の広告は見つかりませんでした。"]
    if reason:
        message.extend(["", f"補足: {reason}"])
    post_slack_message("\n".join(message))

# --- 広告評価ロジック ---
def evaluate_account(account_id):
    print(f"=== {account_id} の広告を評価中 ===")
    campaign_ids = get_campaign_ids()
    if not campaign_ids:
        print(f"[スキップ] {account_id} の広告は、キャンペーンIDが未指定のため評価対象外")
        notify_no_stop_candidates(account_id, "キャンペーンIDが未指定です")
        return

    ads = fetch_ad_ids(account_id, campaign_ids=campaign_ids)

    if not ads:
        notify_no_stop_candidates(account_id, "アクティブな広告を取得できませんでした")
        return

    ads_with_insights = []
    for ad in ads:
        insights = fetch_ad_insights(ad["id"])
        ad["insights"] = insights
        ads_with_insights.append(ad)

    ads_with_metrics = []
    for ad in ads_with_insights:
        cpa, ctr = calculate_metrics(ad)
        ads_with_metrics.append((ad, cpa, ctr))

    # 全期間でCVがある広告を保護対象に追加
    protected_ads = []
    for ad, cpa, ctr in ads_with_metrics:
        if has_lifetime_conversions(ad["id"]):
            protected_ads.append(ad)
    
    with_cpa = [entry for entry in ads_with_metrics if entry[1] is not None]
    without_cpa = [entry for entry in ads_with_metrics if entry[1] is None]

    top_ctr_no_cv = sorted(without_cpa, key=lambda x: x[2], reverse=True)[:5]
    winners = [entry[0] for entry in sorted(with_cpa, key=lambda x: x[1])[:1] + top_ctr_no_cv]
    
    # 全期間CVがある広告をwinnersに追加（重複を避ける）
    for ad in protected_ads:
        if ad not in winners:
            winners.append(ad)

    rows_to_write = []
    for ad, cpa, ctr in ads_with_metrics:
        if ad not in winners:
            image_url = fetch_creative_image_url(ad["id"])
            print(f"[通知] {ad['name']} - CPA: {cpa} CTR: {ctr}")
            
            ad_details = fetch_ad_details(ad['id'])
            campaign_name = fetch_campaign_name(ad_details.get("campaign_id", ""))
            adset_name = fetch_adset_name(ad_details.get("adset_id", ""))
            
            # JSONに承認待ちとして追加
            add_pending_approval(
                ad_id=ad['id'],
                ad_name=ad['name'],
                campaign_name=campaign_name,
                adset_name=adset_name,
                cpa=cpa,
                image_url=image_url
            )
            
            # Slack通知
            send_slack_notice(ad, cpa, image_url, label="STOP候補")

            # Google Sheetsへの追加（互換性のため保持）
            rows_to_write.append([
                campaign_name,
                adset_name,
                ad['id'],
                ad['name'],
                cpa if cpa is not None else "N/A",
                image_url
            ])

    if rows_to_write:
        write_rows_to_sheet(rows_to_write)
    else:
        notify_no_stop_candidates(account_id)

# --- Main Entry Point ---
def main():
    if not ACCESS_TOKEN:
        print("[警告] ACCESS_TOKENが未設定のため、評価処理を終了します")
        return

    for aid in get_account_ids():
        evaluate_account(aid)

if __name__ == "__main__":
    main()
