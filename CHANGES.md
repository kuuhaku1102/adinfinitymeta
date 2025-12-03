# 変更内容サマリー

## 🎯 実装した機能

### 1. 全期間CV保護機能

**ファイル**: `meta_abtest_runner.py`

**追加した関数**:
- `fetch_lifetime_insights(ad_id)`: 全期間のインサイトを取得
- `has_lifetime_conversions(ad_id)`: 全期間でCVがあるかチェック

**変更した処理**:
- `evaluate_account()`: 全期間CVがある広告を保護対象に追加

**効果**:
- 過去に1件でもコンバージョンがある広告は停止候補から除外
- 実績のある広告を誤って停止するリスクを回避

---

### 2. Web UIによる承認システム

#### 2.1 承認データ管理（JSON）

**ファイル**: `meta_abtest_runner.py`, `approved_stopper.py`

**追加した関数**:
- `load_approvals()`: JSONから承認データを読み込み
- `save_approvals(data)`: JSONに承認データを保存
- `add_pending_approval()`: 停止候補を承認待ちリストに追加
- `get_approved_ads()`: 承認済み広告を取得
- `mark_ad_as_stopped()`: 広告を停止済みにマーク

**データファイル**: `pending_approvals.json`

**データ構造**:
```json
{
  "ad_id": "広告ID",
  "ad_name": "広告名",
  "campaign_name": "キャンペーン名",
  "adset_name": "広告セット名",
  "cpa": 1500.50,
  "image_url": "画像URL",
  "status": "pending|approved|rejected|stopped",
  "created_at": "作成日時",
  "approved_at": "承認日時",
  "approved_by": "承認者"
}
```

#### 2.2 Web UI（Flask）

**ファイル**: `approval_web.py`, `templates/index.html`

**実装した機能**:
- 承認待ち広告の一覧表示
- 承認済み・却下済み広告の履歴表示
- ワンクリックで承認/却下
- 広告画像、CPA、キャンペーン情報の表示
- レスポンシブデザイン

**APIエンドポイント**:
- `GET /`: 承認画面の表示
- `POST /api/approve/<ad_id>`: 広告の承認
- `POST /api/reject/<ad_id>`: 広告の却下
- `GET /api/approvals`: 承認データの取得（JSON）

#### 2.3 Slack通知の改善

**変更内容**:
- Slack通知にWeb UIへのリンクを追加
- 環境変数`APPROVAL_WEB_URL`でリンク先を設定可能

**通知メッセージの例**:
```
📣 Meta広告通知 [STOP候補]

キャンペーン名: 春キャンペーン
広告セット名: 東京ターゲット
広告名: テスト広告A
CPA: ¥1500.50
広告ID: 120230617419590484
画像URL: https://...

👉 広告停止の承認はこちら
   http://your-server.com:5000
```

#### 2.4 承認済み広告の停止処理

**ファイル**: `approved_stopper.py`

**変更内容**:
- JSONから承認済み広告を読み取り
- 停止完了後、ステータスを`stopped`に更新
- Google Sheetsをフォールバックとして維持（互換性）

---

## 📊 処理フロー比較

### 変更前（Google Sheets）

```
1. meta_abtest_runner.py
   ↓ 停止候補を検出
   ↓ Google Sheetsに書き込み
   ↓ Slackに通知

2. 担当者がGoogle Sheetsを開く
   ↓ 手動で「承認」列に"YES"を入力

3. approved_stopper.py
   ↓ Google Sheetsから"YES"を読み取り
   ↓ Meta APIで広告を停止
   ↓ Slackに完了通知
```

### 変更後（Web UI）

```
1. meta_abtest_runner.py
   ↓ 停止候補を検出
   ↓ pending_approvals.json に記録
   ↓ Slackに通知（Web UIリンク付き）
   ↓ (Google Sheetsにも書き込み - 互換性維持)

2. 担当者がSlackからWeb UIを開く
   ↓ ワンクリックで承認/却下
   ↓ pending_approvals.json が更新

3. approved_stopper.py
   ↓ pending_approvals.json から承認済み広告を取得
   ↓ Meta APIで広告を停止
   ↓ Slackに完了通知
   ↓ pending_approvals.json を更新（stopped）
```

---

## 🔧 環境変数の追加

`.env`ファイルに以下を追加してください：

```bash
# 承認用WebページのURL（本番環境）
APPROVAL_WEB_URL=http://your-server.com:5000
```

---

## 📝 互換性について

### Google Sheetsとの互換性

以下の互換性を維持しています：

1. **meta_abtest_runner.py**
   - JSONへの記録に加えて、Google Sheetsへの書き込みも継続
   - 既存のワークフローに影響なし

2. **approved_stopper.py**
   - 優先的にJSONから承認データを読み取り
   - JSONがない場合、Google Sheetsをフォールバック
   - 段階的な移行が可能

### 移行パス

**段階1**: JSONとGoogle Sheetsを並行運用
- 両方のシステムが動作
- 問題があればGoogle Sheetsに戻せる

**段階2**: Web UIに完全移行
- Google Sheets関連のコードを削除可能
- `write_rows_to_sheet()`の呼び出しを削除

---

## 🚀 起動方法

### Web UIの起動

```bash
# 方法1: 起動スクリプトを使用
./start_web.sh

# 方法2: 直接実行
python3 approval_web.py
```

### 停止候補の検出

```bash
python3 meta_abtest_runner.py
```

### 承認済み広告の停止

```bash
python3 approved_stopper.py
```

---

## 🎨 カスタマイズポイント

### Web UIのデザイン変更

`templates/index.html`を編集：
- CSS部分を変更してカラースキームを調整
- レイアウトの変更
- 追加情報の表示

### 承認フローの拡張

`approval_web.py`に機能追加：
- 承認者名の記録
- コメント機能
- 承認履歴のエクスポート
- 権限管理

### 通知のカスタマイズ

`meta_abtest_runner.py`の`send_slack_notice()`を編集：
- 通知メッセージのフォーマット変更
- 追加情報の表示
- Block Kitを使った高度なレイアウト

---

## 🛡️ セキュリティ考慮事項

### 現在の実装

- 認証機能なし
- HTTPで動作（開発環境）

### 本番環境での推奨事項

1. **認証の追加**
   - Basic認証
   - OAuth 2.0
   - Slack認証

2. **HTTPS化**
   - SSL/TLS証明書の設定
   - Let's Encryptの利用

3. **アクセス制限**
   - IPアドレス制限
   - VPN経由のアクセスのみ許可

4. **監査ログ**
   - 承認/却下の履歴記録
   - 操作者の記録

---

## 📦 必要なパッケージ

```bash
pip3 install flask requests gspread oauth2client python-dotenv
```

---

## 🐛 トラブルシューティング

### Web UIが起動しない

```bash
# Flaskがインストールされているか確認
pip3 show flask

# ポート5000が使用中か確認
lsof -i :5000

# 別のポートで起動
python3 approval_web.py
# approval_web.py内のport=5000を変更
```

### JSONファイルが見つからない

```bash
# JSONファイルを手動作成
echo "[]" > pending_approvals.json
```

### 承認データが反映されない

```bash
# JSONファイルの内容を確認
cat pending_approvals.json | python3 -m json.tool

# 権限を確認
ls -la pending_approvals.json
```

---

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. ログ出力を確認
2. JSONファイルの内容を確認
3. 環境変数が正しく設定されているか確認
4. Meta APIのアクセストークンが有効か確認
