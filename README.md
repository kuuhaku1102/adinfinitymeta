# Meta広告停止承認システム

Googleスプレッドシートの代わりに、簡易Webページで広告停止の承認を行えるシステムです。

## 🎯 システム概要

このシステムは以下の3つのコンポーネントで構成されています：

1. **meta_abtest_runner.py** - 停止候補の検出と通知
2. **approval_web.py** - Web UIによる承認管理
3. **approved_stopper.py** - 承認済み広告の停止実行

## 📋 新機能

### 改善点1: 全期間CV保護機能
- **全期間でコンバージョンがある広告は停止対象から除外**
- 過去に実績のある広告を誤って停止するリスクを回避

### 改善点2: Web UIによる承認フロー
- **Googleスプレッドシートの代わりに簡易Webページで承認**
- Slack通知からWebページへのリンクをクリックして承認/却下
- リアルタイムで承認状態を確認可能

## 🚀 セットアップ

### 1. 環境変数の設定

`.env`ファイルに以下を追加：

```bash
ACCESS_TOKEN=your_meta_access_token
ACCOUNT_IDS=act_123456789,act_987654321
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
APPROVAL_WEB_URL=http://your-server.com:5000  # 本番環境のURL
```

### 2. 依存パッケージのインストール

```bash
pip3 install flask requests gspread oauth2client python-dotenv
```

### 3. Web UIの起動

```bash
cd /home/ubuntu/adinfinitymeta
python3 approval_web.py
```

デフォルトでは `http://localhost:5000` でアクセス可能です。

## 📖 使い方

### ステップ1: 停止候補の検出

```bash
python3 meta_abtest_runner.py
```

**実行内容**：
- 指定されたキャンペーンの広告を評価
- 停止候補を`pending_approvals.json`に記録
- Slackに通知（Web UIへのリンク付き）

**停止候補の選定ロジック**：
- ✅ **保護対象（停止しない）**
  - CPAが最も低い広告 1件
  - CTRが高い広告 上位5件
  - **全期間でCVがある広告すべて** ← 新機能
- ❌ **停止候補**
  - 上記以外の広告

### ステップ2: Web UIで承認

1. Slackの通知からWebページのリンクをクリック
2. 承認待ちの広告一覧を確認
3. 各広告の「✅ 停止を承認」または「❌ 却下」ボタンをクリック

**Web UIの機能**：
- 承認待ち、承認済み、却下済みの広告を分類表示
- 広告画像、CPA、キャンペーン名などの詳細情報を表示
- ワンクリックで承認/却下

### ステップ3: 承認済み広告の停止実行

```bash
python3 approved_stopper.py
```

**実行内容**：
- `pending_approvals.json`から承認済み広告を取得
- Meta Graph APIで広告を`PAUSED`に変更
- Slackに停止完了通知を送信
- 広告を`stopped`ステータスに更新

## 📁 ファイル構造

```
adinfinitymeta/
├── meta_abtest_runner.py      # 停止候補の検出
├── approval_web.py             # Web UI（Flask）
├── approved_stopper.py         # 承認済み広告の停止
├── pending_approvals.json      # 承認データ（自動生成）
├── templates/
│   └── index.html             # Web UIのテンプレート
├── .env                        # 環境変数
└── README.md                   # このファイル
```

## 🔄 データフロー

```
1. meta_abtest_runner.py
   ↓ 停止候補を検出
   ↓ pending_approvals.json に記録
   ↓ Slackに通知（Web UIリンク付き）

2. approval_web.py（Web UI）
   ↓ ユーザーが承認/却下
   ↓ pending_approvals.json を更新

3. approved_stopper.py
   ↓ 承認済み広告を取得
   ↓ Meta APIで広告を停止
   ↓ Slackに完了通知
   ↓ pending_approvals.json を更新（stopped）
```

## 📊 JSONデータ構造

`pending_approvals.json`の例：

```json
[
  {
    "ad_id": "120230617419590484",
    "ad_name": "テスト広告A",
    "campaign_name": "春キャンペーン",
    "adset_name": "東京ターゲット",
    "cpa": 1500.50,
    "image_url": "https://example.com/image.jpg",
    "status": "pending",
    "created_at": "2025-12-03T10:30:00",
    "approved_at": null,
    "approved_by": null
  }
]
```

**ステータスの種類**：
- `pending`: 承認待ち
- `approved`: 承認済み（停止実行待ち）
- `rejected`: 却下
- `stopped`: 停止完了

## 🔧 本番環境での運用

### Web UIの公開

本番環境では、以下のいずれかの方法でWeb UIを公開してください：

1. **ngrokを使用（開発・テスト用）**
   ```bash
   ngrok http 5000
   ```
   生成されたURLを`APPROVAL_WEB_URL`に設定

2. **本番サーバーでの運用**
   - Nginx + Gunicornなどで運用
   - HTTPSを推奨
   - 認証機能の追加を検討

### 定期実行の設定

cronで定期実行する例：

```bash
# 毎日午前9時に停止候補を検出
0 9 * * * cd /home/ubuntu/adinfinitymeta && python3 meta_abtest_runner.py

# 毎時間、承認済み広告を停止
0 * * * * cd /home/ubuntu/adinfinitymeta && python3 approved_stopper.py
```

## 🛡️ 互換性

- Google Sheetsとの互換性を維持
- `meta_abtest_runner.py`は引き続きGoogle Sheetsにも書き込み
- `approved_stopper.py`はJSONがない場合、Google Sheetsをフォールバック

## 🎨 Web UIのカスタマイズ

`templates/index.html`を編集することで、デザインや機能をカスタマイズできます：

- 色やレイアウトの変更
- 承認者名の記録
- フィルター機能の追加
- 統計情報の表示

## 📝 注意事項

- `pending_approvals.json`は自動生成されるため、手動編集は非推奨
- Web UIは認証機能がないため、社内ネットワークでの運用を推奨
- 本番環境では必ずHTTPSを使用してください
