# Slackリアクション方式 クイックスタート 🚀

**最も簡単な方法**：サーバー不要、インストール不要、Slackだけで完結！

## 🎯 この方式の特徴

- ✅ **サーバー不要** - 自分のPCで実行
- ✅ **インストール不要** - ngrokなどの追加ツール不要
- ✅ **Slackだけで完結** - 絵文字リアクションで承認/却下
- ✅ **シンプル** - 設定は5分で完了

## 📋 セットアップ（5分）

### ステップ1: Slack Appの作成

1. https://api.slack.com/apps にアクセス
2. 「Create New App」→「From scratch」
3. App名: `Meta広告承認Bot`
4. ワークスペースを選択

### ステップ2: 権限の設定

「OAuth & Permissions」→「Bot Token Scopes」で以下を追加：

- `channels:history` - メッセージ履歴を読む
- `reactions:read` - リアクションを読む
- `chat:write` - メッセージを送信

### ステップ3: Botをインストール

1. 「Install to Workspace」をクリック
2. **Bot User OAuth Token**（`xoxb-`で始まる）をコピー

### ステップ4: Botをチャンネルに追加

Slackチャンネルで以下を実行：

```
/invite @Meta広告承認Bot
```

### ステップ5: 環境変数を設定

`.env`ファイルに追加：

```bash
# Slack Bot Token
SLACK_BOT_TOKEN=xoxb-your-bot-token-here

# 通知を送るチャンネルID
SLACK_CHANNEL_ID=C01234567890
```

**チャンネルIDの確認方法**：
- Slackでチャンネルを開く
- チャンネル名をクリック
- 下部の「チャンネルID」をコピー

### ステップ6: 動作確認

```bash
cd /home/ubuntu/adinfinitymeta
python3 slack_reaction_helper.py
```

成功すると：
```
✅ Slack接続成功
   Bot名: Meta広告承認Bot
   チーム: Your Workspace
```

## 🎮 使い方

### 1. 停止候補を検出

```bash
python3 meta_abtest_runner.py
```

Slackに以下のような通知が届きます：

```
📣 Meta広告通知 [STOP候補]

キャンペーン名: 春キャンペーン
広告セット名: 東京ターゲット
広告名: テスト広告A
CPA: ¥1500.50
広告ID: 120230617419590484
画像URL: https://...

👍 このメッセージに絵文字でリアクション:
  ✅ = 停止を承認
  ❌ = 却下
```

### 2. 絵文字でリアクション

Slackのメッセージに絵文字を追加：

- **✅** (`:white_check_mark:`) をクリック → 停止を承認
- **❌** (`:x:`) をクリック → 却下

### 3. 承認済み広告を停止

```bash
python3 approved_stopper.py
```

✅リアクションがついた広告が自動的に停止されます。

## 🔄 処理フロー

```
1. meta_abtest_runner.py
   ↓ 停止候補を検出
   ↓ Slackに通知（Bot Token使用）
   ↓ メッセージIDを記録

2. 担当者がSlackでリアクション
   ↓ ✅ = 承認
   ↓ ❌ = 却下

3. approved_stopper.py
   ↓ リアクションを読み取り
   ↓ ✅がついた広告を停止
   ↓ Slackに完了通知
```

## 📊 データ管理

リアクション情報は`slack_reactions.json`に記録されます：

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

**ステータス**：
- `pending`: リアクション待ち
- `approved`: ✅リアクションあり
- `stopped`: 停止完了

## 🔧 定期実行（オプション）

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

## 🐛 トラブルシューティング

### "not_in_channel" エラー

Botがチャンネルに追加されていません。

```bash
/invite @Meta広告承認Bot
```

### "invalid_auth" エラー

Bot Tokenが間違っています。`.env`ファイルを確認してください。

### リアクションが読み取れない

1. Bot Tokenに`reactions:read`権限があるか確認
2. Botがチャンネルに追加されているか確認
3. チャンネルIDが正しいか確認

### メッセージが送信されない

1. Bot Tokenに`chat:write`権限があるか確認
2. チャンネルIDが正しいか確認
3. Botがチャンネルに追加されているか確認

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

## 🎉 完了！

これでSlack絵文字リアクションによる承認が使えます。
最もシンプルで、追加のインストールやサーバーが不要です！

## 📚 関連ドキュメント

- **SLACK_BOT_SETUP.md** - 詳細なセットアップ手順
- **README.md** - システム全体の説明
- **CHANGES.md** - 変更内容の詳細
