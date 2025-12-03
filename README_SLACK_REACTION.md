# Meta広告停止承認システム（Slackリアクション方式）

**最もシンプルな承認方式**：サーバー不要、Slackの絵文字リアクションだけで完結！

## 🎯 システム概要

このシステムは以下の3つのコンポーネントで構成されています：

1. **meta_abtest_runner.py** - 停止候補の検出と通知
2. **slack_reaction_helper.py** - Slackリアクションの管理
3. **approved_stopper.py** - 承認済み広告の停止実行

## ✨ 主な機能

### 1. 全期間CV保護機能
- 全期間でコンバージョンがある広告は停止対象から除外
- 過去に実績のある広告を誤って停止するリスクを回避

### 2. Slack絵文字リアクション承認
- Slackメッセージに✅でリアクション → 承認
- ❌でリアクション → 却下
- サーバー不要、インストール不要

## 🚀 クイックスタート

### 1. Slack Botのセットアップ（5分）

詳細は `SLACK_BOT_SETUP.md` を参照してください。

**簡単な手順**：
1. https://api.slack.com/apps でSlack Appを作成
2. 権限を追加：`channels:history`, `reactions:read`, `chat:write`
3. Bot Tokenを取得（`xoxb-`で始まる）
4. Botをチャンネルに追加：`/invite @Bot名`

### 2. 環境変数の設定

`.env`ファイルに追加：

```bash
# Meta広告API
ACCESS_TOKEN=your_meta_access_token
ACCOUNT_IDS=act_123456789,act_987654321

# Slack Bot Token（新規）
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_CHANNEL_ID=C01234567890

# Slack Webhook URL（既存、通知用として継続利用可能）
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. 動作確認

```bash
# Slack接続テスト
python3 test_slack_bot.py

# Slackでメッセージにリアクション後
python3 test_slack_reactions.py
```

## 📖 使い方

### ステップ1: 停止候補の検出

```bash
python3 meta_abtest_runner.py
```

**実行内容**：
- 指定されたキャンペーンの広告を評価
- 停止候補をSlackに通知（Bot Token使用）
- メッセージIDを`slack_reactions.json`に記録

**停止候補の選定ロジック**：
- ✅ **保護対象（停止しない）**
  - CPAが最も低い広告 1件
  - CTRが高い広告 上位5件
  - **全期間でCVがある広告すべて** ← 新機能
- ❌ **停止候補**
  - 上記以外の広告

### ステップ2: Slackでリアクション

Slackの通知メッセージに絵文字でリアクション：

- **✅** (`:white_check_mark:`) → 停止を承認
- **❌** (`:x:`) → 却下

### ステップ3: 承認済み広告の停止

```bash
python3 approved_stopper.py
```

**実行内容**：
- Slackリアクションを読み取り
- ✅がついた広告を停止
- Slackに完了通知を送信
- `slack_reactions.json`を更新（stopped）

## 🔄 処理フロー

```
1. meta_abtest_runner.py
   ↓ 停止候補を検出
   ↓ Slackに通知（Bot Token使用）
   ↓ slack_reactions.json にメッセージIDを記録

2. 担当者がSlackでリアクション
   ↓ ✅ = 承認
   ↓ ❌ = 却下

3. approved_stopper.py
   ↓ Slackリアクションを読み取り
   ↓ ✅がついた広告を停止
   ↓ Slackに完了通知
   ↓ slack_reactions.json を更新（stopped）
```

## 📁 ファイル構造

```
adinfinitymeta/
├── meta_abtest_runner.py           # 停止候補の検出
├── slack_reaction_helper.py        # Slackリアクション管理
├── approved_stopper.py             # 承認済み広告の停止
├── slack_reactions.json            # リアクションデータ（自動生成）
├── test_slack_bot.py               # Slack接続テスト
├── test_slack_reactions.py         # リアクション読み取りテスト
├── .env                            # 環境変数
├── README_SLACK_REACTION.md        # このファイル
├── SLACK_BOT_SETUP.md              # 詳細セットアップガイド
└── SLACK_REACTION_QUICKSTART.md    # クイックスタート
```

## 📊 データ構造

### slack_reactions.json

```json
[
  {
    "ad_id": "120230617419590484",
    "message_ts": "1234567890.123456",
    "channel_id": "C01234567890",
    "created_at": "2025-12-03T10:30:00",
    "status": "pending"
  }
]
```

**ステータスの種類**：
- `pending`: リアクション待ち
- `approved`: ✅リアクションあり（停止実行待ち）
- `stopped`: 停止完了

## 🔧 定期実行

cronで定期実行する場合：

```bash
crontab -e
```

以下を追加：

```bash
# 毎日午前9時に停止候補を検出
0 9 * * * cd /home/ubuntu/adinfinitymeta && python3 meta_abtest_runner.py

# 毎時間、承認済み広告を停止
0 * * * * cd /home/ubuntu/adinfinitymeta && python3 approved_stopper.py
```

## 🛡️ 互換性

### Google Sheetsとの互換性

以下の互換性を維持しています：

1. **meta_abtest_runner.py**
   - Slackリアクション方式に加えて、Google Sheetsへの書き込みも継続
   - 既存のワークフローに影響なし

2. **approved_stopper.py**
   - 優先的にSlackリアクションから承認データを読み取り
   - JSONファイル（Web UI）もサポート
   - Google Sheetsをフォールバック

### Web UIとの互換性

- Slackリアクション方式とWeb UI方式を並行利用可能
- `pending_approvals.json`と`slack_reactions.json`の両方をサポート

## 🐛 トラブルシューティング

### "not_in_channel" エラー

Botがチャンネルに追加されていません。

```bash
/invite @Meta広告承認Bot
```

### "invalid_auth" エラー

Bot Tokenが間違っています。`.env`ファイルを確認してください。

### リアクションが読み取れない

```bash
# テストスクリプトで確認
python3 test_slack_reactions.py
```

確認事項：
1. Bot Tokenに`reactions:read`権限があるか
2. Botがチャンネルに追加されているか
3. チャンネルIDが正しいか

### メッセージが送信されない

```bash
# テストスクリプトで確認
python3 test_slack_bot.py
```

確認事項：
1. Bot Tokenに`chat:write`権限があるか
2. チャンネルIDが正しいか
3. Botがチャンネルに追加されているか

## 💡 Tips

### 複数人で承認

- 誰がリアクションしても承認されます
- 最初に✅をつけた人が承認者になります

### 承認の取り消し

- リアクションを削除すれば承認を取り消せます
- ただし、`approved_stopper.py`実行前に限ります

### 履歴の確認

```bash
# リアクションデータを確認
cat slack_reactions.json | python3 -m json.tool
```

## 📚 ドキュメント

- **SLACK_REACTION_QUICKSTART.md** - 最速で始める手順
- **SLACK_BOT_SETUP.md** - 詳細なセットアップ手順
- **README.md** - システム全体の説明
- **CHANGES.md** - 変更内容の詳細

## 🎉 まとめ

Slackリアクション方式は、以下の点で最もシンプルです：

- ✅ サーバー不要
- ✅ ngrokなどの追加ツール不要
- ✅ Slackだけで完結
- ✅ 設定は5分で完了

質問や問題があれば、各ドキュメントを参照してください。
