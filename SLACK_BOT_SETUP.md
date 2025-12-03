# Slack Bot Token セットアップガイド

Slack絵文字リアクションで承認/却下を行うための設定手順です。

## 🎯 必要なもの

- Slackワークスペースの管理者権限（またはApp追加権限）
- 5分程度の時間

## 📋 セットアップ手順

### ステップ1: Slack Appの作成

1. https://api.slack.com/apps にアクセス
2. 「Create New App」をクリック
3. 「From scratch」を選択
4. App名を入力（例: `Meta広告承認Bot`）
5. ワークスペースを選択
6. 「Create App」をクリック

### ステップ2: Bot Token Scopesの設定

1. 左メニューから「OAuth & Permissions」をクリック
2. 「Scopes」セクションまでスクロール
3. 「Bot Token Scopes」で以下を追加：

   **必須の権限**：
   - `channels:history` - チャンネルのメッセージを読む
   - `reactions:read` - リアクションを読む
   - `chat:write` - メッセージを送信（既存のWebhookの代わり）

   **追加方法**：
   - 「Add an OAuth Scope」をクリック
   - 上記の権限を1つずつ追加

### ステップ3: Botをワークスペースにインストール

1. 「OAuth & Permissions」ページの上部にある「Install to Workspace」をクリック
2. 権限の確認画面で「許可する」をクリック
3. **Bot User OAuth Token**が表示されます
   - `xoxb-`で始まる長い文字列
   - これをコピーして保存

### ステップ4: BotをチャンネルにInvite

1. Slackで通知を受け取りたいチャンネルを開く
2. チャンネル名をクリック → 「インテグレーション」タブ
3. 「アプリを追加する」をクリック
4. 作成したBot（例: `Meta広告承認Bot`）を選択

または、チャンネルで以下のコマンドを実行：
```
/invite @Meta広告承認Bot
```

### ステップ5: 環境変数の設定

`.env`ファイルに以下を追加：

```bash
# Slack Bot Token（xoxb-で始まる）
SLACK_BOT_TOKEN=xoxb-your-bot-token-here

# Slack通知を送るチャンネルID
SLACK_CHANNEL_ID=C01234567890
```

**チャンネルIDの確認方法**：
1. Slackでチャンネルを開く
2. チャンネル名をクリック
3. 下部に表示される「チャンネルID」をコピー
   - または、URLの最後の部分（例: `C01234567890`）

### ステップ6: 動作確認

```bash
cd /home/ubuntu/adinfinitymeta
python3 test_slack_bot.py
```

成功すると、Slackチャンネルにテストメッセージが送信されます。

## 🎨 使い方

### 1. 停止候補の通知

`meta_abtest_runner.py`を実行すると、Slackに通知が送信されます：

```
📣 Meta広告通知 [STOP候補]

キャンペーン名: 春キャンペーン
広告セット名: 東京ターゲット
広告名: テスト広告A
CPA: ¥1500.50
広告ID: 120230617419590484

👍 このメッセージに絵文字でリアクション:
  ✅ = 停止を承認
  ❌ = 却下
```

### 2. 絵文字でリアクション

- **✅ (`:white_check_mark:`)** をクリック → 停止を承認
- **❌ (`:x:`)** をクリック → 却下

### 3. 承認済み広告の停止

`approved_stopper.py`を実行すると：
- ✅リアクションがついたメッセージから広告IDを取得
- 該当する広告を停止
- 停止完了通知を送信

## 🔧 トラブルシューティング

### "not_in_channel" エラー

Botがチャンネルに追加されていません。

```bash
/invite @Meta広告承認Bot
```

### "missing_scope" エラー

必要な権限が不足しています。
「OAuth & Permissions」で権限を追加後、Botを再インストールしてください。

### チャンネルIDがわからない

```bash
# Slackで以下のコマンドを実行
/channel-info
```

または、ブラウザのURLから確認：
```
https://app.slack.com/client/T01234/C01234567890
                                    ↑ これがチャンネルID
```

## 🔐 セキュリティ

### Bot Tokenの管理

- **絶対に公開しない**（GitHubなどにコミットしない）
- `.env`ファイルに保存
- `.gitignore`に`.env`を追加

### 権限の最小化

必要最小限の権限のみを付与してください：
- `channels:history` - メッセージ履歴の読み取り
- `reactions:read` - リアクションの読み取り
- `chat:write` - メッセージ送信

## 📝 Webhook URLとの違い

### Webhook URL（既存）
- ✅ メッセージ送信のみ
- ❌ リアクション読み取り不可
- ❌ メッセージ履歴読み取り不可

### Bot Token（新規）
- ✅ メッセージ送信
- ✅ リアクション読み取り
- ✅ メッセージ履歴読み取り

**両方使えます**：
- Webhook URLは通知専用として継続利用可能
- Bot Tokenはリアクション読み取り用

## 🎉 完了！

これでSlack絵文字リアクションによる承認が可能になります。
