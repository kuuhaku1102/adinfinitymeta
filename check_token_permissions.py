#!/usr/bin/env python3
"""
アクセストークンの権限を確認するスクリプト
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

def check_token_permissions():
    """アクセストークンの権限を確認"""
    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKENが設定されていません")
        return
    
    # デバッグ情報APIを使用
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
            
            print("=" * 60)
            print("アクセストークン情報")
            print("=" * 60)
            print(f"アプリID: {token_data.get('app_id')}")
            print(f"ユーザーID: {token_data.get('user_id')}")
            print(f"有効期限: {token_data.get('expires_at', '無期限')}")
            print(f"トークンタイプ: {token_data.get('type')}")
            print(f"有効: {token_data.get('is_valid')}")
            
            # 権限を表示
            scopes = token_data.get("scopes", [])
            print(f"\n権限一覧 ({len(scopes)}個):")
            for scope in sorted(scopes):
                print(f"  ✓ {scope}")
            
            # 必要な権限をチェック
            print("\n" + "=" * 60)
            print("必要な権限のチェック")
            print("=" * 60)
            
            required_permissions = [
                "ads_management",
                "ads_read",
                "business_management"
            ]
            
            for perm in required_permissions:
                if perm in scopes:
                    print(f"  ✅ {perm}: あり")
                else:
                    print(f"  ❌ {perm}: なし")
            
            print("=" * 60)
            
        else:
            print(f"❌ トークン情報取得失敗: {res.status_code}")
            print(f"レスポンス: {res.text}")
    
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_token_permissions()
