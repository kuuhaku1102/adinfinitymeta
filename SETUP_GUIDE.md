# セットアップガイド

このガイドでは、Meta広告自動化システムを実際に動かすための具体的な手順を説明します。

## 📋 目次

1. [環境構築](#環境構築)
2. [リポジトリのクローン](#リポジトリのクローン)
3. [依存関係のインストール](#依存関係のインストール)
4. [Meta広告APIの設定](#meta広告apiの設定)
5. [Slack Botの設定](#slack-botの設定)
6. [.envファイルの設定](#envファイルの設定)
7. [動作確認](#動作確認)
8. [実行方法](#実行方法)

---

## 1. 環境構築

### 必要な環境

- **Python 3.11以上**
- **Git**
- **インターネット接続**

### Pythonのインストール確認

```bash
python3 --version
# または
python --version
```

`Python 3.11.x`以上が表示されればOKです。

### インストールされていない場合

**macOS:**
```bash
brew install python@3.11
```

**Ubuntu/Linux:**
```bash
sudo apt update
sudo apt install python3.11 python3-pip
```

**Windows:**
[Python公式サイト](https://www.python.org/downloads/)からインストーラーをダウンロード

---

## 2. リポジトリのクローン

```bash
# リポジトリをクローン
git clone https://github.com/kuuhaku1102/adinfinitymeta.git

# ディレクトリに移動
cd adinfinitymeta
```

---

## 3. 依存関係のインストール

### 必要なPythonパッケージ

```bash
pip3 install requests python-dotenv gspread oauth2client
```

または

```bash
pip install requests python-dotenv gspread oauth2client
```

### インストール確認

```bash
pip3 list | grep -E "requests|python-dotenv|gspread"
```

以下のように表示されればOK:
```
python-dotenv    1.2.1
requests         2.31.0
gspread          5.12.0
oauth2client     4.1.3
```

---

## 4. Meta広告APIの設定

### 4.1 Meta Access Tokenの取得

1. **Meta Business Suite**にアクセス
   - https://business.facebook.com/

2. **ビジネス設定**を開く
   - 左下の歯車アイコンをクリック

3. **システムユーザー**を作成
   - 「ユーザー」→「システムユーザー」→「システムユーザーを追加」
   - 名前: `Meta広告自動化Bot`
   - 役割: `管理者`

4. **アクセストークンを生成**
   - 作成したシステムユーザーをクリック
   - 「トークンを生成」をクリック
   - アプリを選択（または新規作成）
   - 以下の権限を選択:
     - `ads_management`
     - `ads_read`
     - `business_management`
   - 「トークンを生成」をクリック
   - **トークンをコピー**（`EAAA...`で始まる長い文字列）

5. **広告アカウントに権限を付与**
   - 「広告アカウント」タブ
   - 対象の広告アカウントを選択
   - システムユーザーに権限を付与

### 4.2 広告アカウントIDの確認

1. **Meta広告マネージャ**にアクセス
   - https://adsmanager.facebook.com/

2. URLから広告アカウントIDを確認
   ```
   https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=123456789
                                                                 ↑
                                                          これが広告アカウントID
   ```

3. `act_`を含めた形式でメモ
   - 例: `act_123456789`

---

## 5. Slack Botの設定

### 5.1 Slack Appの作成

1. **Slack API**にアクセス
   - https://api.slack.com/apps

2. **「Create New App」**をクリック
   - 「From scratch」を選択
   - App名: `Meta広告承認Bot`
   - ワークスペースを選択

### 5.2 Bot権限の追加

1. **「OAuth & Permissions」**をクリック

2. **「Bot Token Scopes」**に以下を追加:
   - `channels:history` - チャンネル履歴の読み取り
   - `reactions:read` - リアクションの読み取り
   - `chat:write` - メッセージの送信

### 5.3 Botのインストール

1. **「Install to Workspace」**をクリック

2. **Bot User OAuth Token**をコピー
   - `xoxb-`で始まる長い文字列

### 5.4 チャンネルIDの取得

1. Slackで通知を送りたいチャンネルを開く

2. チャンネル名をクリック

3. 下部に表示される**「チャンネルID」**をコピー
   - `C`で始まる文字列（例: `C01234567890`）

### 5.5 Botをチャンネルに追加

Slackのチャンネルで以下を実行:
```
/invite @Meta広告承認Bot
```

---

## 6. .envファイルの設定

### 6.1 .envファイルを作成

プロジェクトのルートディレクトリに`.env`ファイルを作成:

```bash
cd adinfinitymeta
touch .env
```

### 6.2 .envファイルを編集

以下の内容を`.env`ファイルに記述:

```bash
# Meta広告API
ACCESS_TOKEN=EAAA...（Meta Access Token）
ACCOUNT_IDS=act_123456789（広告アカウントID）

# Slack Bot
SLACK_BOT_TOKEN=xoxb-...（Slack Bot Token）
SLACK_CHANNEL_ID=C01234567890（チャンネルID）

# オプション: Slack Webhook（使わない場合はコメントアウト）
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# オプション: Google Sheets（使わない場合はコメントアウト）
# SPREADSHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID
# GSHEET_JSON={"type":"service_account",...}
```

### 6.3 実際の例

```bash
# Meta広告API
ACCESS_TOKEN=EAAA...(実際のトークン)
ACCOUNT_IDS=act_123456789

# Slack Bot
SLACK_BOT_TOKEN=xoxb-...（実際のトークン）
SLACK_CHANNEL_ID=C01234567890
```

### 6.4 .envファイルの確認

```bash
cat .env
```

正しく設定されているか確認してください。

---

## 7. 動作確認

### 7.1 Slack接続テスト

```bash
python3 test_slack_bot.py
```

**成功例:**
```
✅ Slack接続成功
   Bot名: meta
   チーム: InfinityDesign
✅ Slackメッセージ送信成功
```

Slackチャンネルにテストメッセージが届いていればOKです。

### 7.2 Slackリアクションテスト

1. テストメッセージに✅でリアクション

2. 以下を実行:
```bash
python3 test_slack_reactions.py
```

**成功例:**
```
✅ 承認済み広告: 1件
   - test_ad_id
```

### 7.3 Block Kitテスト

```bash
python3 test_block_kit_message.py
```

Slackに画像付きのリッチなメッセージが届いていればOKです。

---

## 8. 実行方法

### 8.1 広告停止候補の検出

```bash
python3 meta_abtest_runner.py
```

**処理内容:**
- Meta広告APIから広告データを取得
- 停止候補を分析（全期間CV保護を適用）
- Slackに通知

**Slackでの操作:**
- ✅ = 停止を承認
- ❌ = 却下

### 8.2 承認済み広告の停止

```bash
python3 approved_stopper.py
```

**処理内容:**
- ✅リアクションがついた広告を取得
- Meta APIで広告を停止
- Slackに完了通知

### 8.3 広告コピー（インプレッション500以下）

```bash
TARGET_ADSET_ID=123456789 python3 ad_copy_low_impression.py
```

**処理内容:**
- インプレッション500以下の広告を抽出
- V2広告セットを作成
- 広告をコピー（停止状態）
- Slackに通知

**広告セットIDの確認方法:**
1. Meta広告マネージャを開く
2. 広告セットをクリック
3. URLから広告セットIDを確認
   ```
   https://adsmanager.facebook.com/adsmanager/manage/adsets?act=123456789&selected_adset_ids=987654321
                                                                                           ↑
                                                                                    これが広告セットID
   ```

### 8.4 パフォーマンス比較（1週間後）

```bash
python3 compare_adset_performance.py
```

**処理内容:**
- 最新のコピー履歴を取得
- 元の広告セット vs V2のパフォーマンスを比較
- Slackに結果を通知

---

## 🔧 トラブルシューティング

### エラー: ACCESS_TOKENが未設定

**原因:** `.env`ファイルが正しく読み込まれていない

**解決方法:**
1. `.env`ファイルが存在するか確認
2. `python-dotenv`がインストールされているか確認
3. `.env`ファイルの内容を確認

### エラー: Slack接続失敗

**原因:** Slack Bot Tokenが無効

**解決方法:**
1. Slack Bot Tokenが正しいか確認
2. Botがワークスペースにインストールされているか確認
3. Botがチャンネルに追加されているか確認

### エラー: Meta API接続失敗

**原因:** Access Tokenが無効または権限不足

**解決方法:**
1. Access Tokenが正しいか確認
2. トークンの有効期限を確認
3. 必要な権限が付与されているか確認

### エラー: 広告が見つからない

**原因:** 広告アカウントIDまたはキャンペーンIDが間違っている

**解決方法:**
1. `.env`ファイルの`ACCOUNT_IDS`を確認
2. Meta広告マネージャでIDを再確認

---

## 📚 次のステップ

### 定期実行の設定

cronやGitHub Actionsで定期実行を設定できます。

**cron例（毎日午前9時に実行）:**
```bash
crontab -e
```

以下を追加:
```
0 9 * * * cd /path/to/adinfinitymeta && python3 meta_abtest_runner.py
```

### GitHub Actionsでの自動実行

`.github/workflows/`にワークフローファイルを作成することで、GitHub上で自動実行できます。

詳細は`AD_COPY_GUIDE.md`を参照してください。

---

## 🆘 サポート

問題が解決しない場合は、以下の情報を含めてお問い合わせください:

- エラーメッセージの全文
- 実行したコマンド
- `.env`ファイルの内容（トークンは伏せる）
- Python、OSのバージョン

---

## ✅ セットアップ完了チェックリスト

- [ ] Python 3.11以上がインストールされている
- [ ] リポジトリをクローンした
- [ ] 依存関係をインストールした
- [ ] Meta Access Tokenを取得した
- [ ] Slack Bot Tokenを取得した
- [ ] `.env`ファイルを作成・設定した
- [ ] Slack接続テストが成功した
- [ ] Slackリアクションテストが成功した
- [ ] Block Kitテストが成功した

すべてチェックが入れば、実際の運用が可能です！🎉
