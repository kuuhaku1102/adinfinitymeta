# クイックスタート（5分で始める）

最速でMeta広告自動化システムを動かすためのガイドです。

## 📦 1. リポジトリをクローン

```bash
git clone https://github.com/kuuhaku1102/adinfinitymeta.git
cd adinfinitymeta
```

## 🔧 2. 依存関係をインストール

```bash
pip3 install -r requirements.txt
```

## 🔑 3. .envファイルを作成

```bash
cat << 'EOF' > .env
# Meta広告API
ACCESS_TOKEN=ここにMeta Access Tokenを入力
ACCOUNT_IDS=act_123456789

# Slack Bot
SLACK_BOT_TOKEN=xoxb-ここにSlack Bot Tokenを入力
SLACK_CHANNEL_ID=C01234567890
EOF
```

**必要な情報:**
- **Meta Access Token**: [Meta Business Suite](https://business.facebook.com/) → システムユーザー → トークンを生成
- **広告アカウントID**: [Meta広告マネージャ](https://adsmanager.facebook.com/) のURLから確認
- **Slack Bot Token**: [Slack API](https://api.slack.com/apps) → OAuth & Permissions
- **チャンネルID**: Slackのチャンネル情報から確認

詳細は [SETUP_GUIDE.md](SETUP_GUIDE.md) を参照してください。

## ✅ 4. 動作確認

```bash
# Slack接続テスト
python3 test_slack_bot.py
```

成功すると、Slackにテストメッセージが届きます。

## 🚀 5. 実行

### 広告停止候補の検出

```bash
python3 meta_abtest_runner.py
```

Slackに通知が届いたら、✅または❌でリアクションしてください。

### 承認済み広告の停止

```bash
python3 approved_stopper.py
```

✅をつけた広告が停止されます。

### 広告コピー（インプレッション500以下）

```bash
TARGET_ADSET_ID=123456789 python3 ad_copy_low_impression.py
```

V2広告セットが作成され、広告がコピーされます。

## 📚 詳細ドキュメント

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - 詳細なセットアップ手順
- **[SLACK_REACTION_QUICKSTART.md](SLACK_REACTION_QUICKSTART.md)** - Slack承認機能の使い方
- **[AD_COPY_GUIDE.md](AD_COPY_GUIDE.md)** - 広告コピー機能の使い方
- **[README_SLACK_REACTION.md](README_SLACK_REACTION.md)** - 完全ガイド

## 🆘 トラブルシューティング

### エラーが出る場合

1. Python 3.11以上がインストールされているか確認
   ```bash
   python3 --version
   ```

2. 依存関係が正しくインストールされているか確認
   ```bash
   pip3 list | grep -E "requests|python-dotenv"
   ```

3. `.env`ファイルが正しく設定されているか確認
   ```bash
   cat .env
   ```

詳細は [SETUP_GUIDE.md](SETUP_GUIDE.md) のトラブルシューティングを参照してください。

---

**準備ができたら、実際に動かしてみましょう！** 🎉
