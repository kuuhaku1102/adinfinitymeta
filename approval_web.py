import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

APPROVAL_FILE = "pending_approvals.json"

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

@app.route('/')
def index():
    """承認待ちの広告一覧を表示"""
    approvals = load_approvals()
    pending = [a for a in approvals if a.get('status') == 'pending']
    approved = [a for a in approvals if a.get('status') == 'approved']
    rejected = [a for a in approvals if a.get('status') == 'rejected']
    
    return render_template('index.html', 
                         pending=pending, 
                         approved=approved, 
                         rejected=rejected)

@app.route('/api/approve/<ad_id>', methods=['POST'])
def approve_ad(ad_id):
    """広告を承認する"""
    approvals = load_approvals()
    updated = False
    
    for ad in approvals:
        if ad.get('ad_id') == ad_id and ad.get('status') == 'pending':
            ad['status'] = 'approved'
            ad['approved_at'] = datetime.now().isoformat()
            updated = True
            break
    
    if updated:
        save_approvals(approvals)
        return jsonify({'success': True, 'message': '承認しました'})
    else:
        return jsonify({'success': False, 'message': '広告が見つかりません'}), 404

@app.route('/api/reject/<ad_id>', methods=['POST'])
def reject_ad(ad_id):
    """広告を却下する"""
    approvals = load_approvals()
    updated = False
    
    for ad in approvals:
        if ad.get('ad_id') == ad_id and ad.get('status') == 'pending':
            ad['status'] = 'rejected'
            ad['approved_at'] = datetime.now().isoformat()
            updated = True
            break
    
    if updated:
        save_approvals(approvals)
        return jsonify({'success': True, 'message': '却下しました'})
    else:
        return jsonify({'success': False, 'message': '広告が見つかりません'}), 404

@app.route('/api/approvals')
def get_approvals():
    """承認データをJSON形式で取得"""
    approvals = load_approvals()
    return jsonify(approvals)

if __name__ == '__main__':
    # テンプレートディレクトリが存在しない場合は作成
    os.makedirs('templates', exist_ok=True)
    
    # 開発環境での実行
    app.run(host='0.0.0.0', port=5000, debug=True)
