# クイックスタートガイド 🚀

最速で動かすための手順です。

## 📋 前提条件

- Python 3.7以上
- Meta広告のアクセストークン
- Slack Webhook URL

## ⚡ 3ステップで起動

### ステップ1: ngrokのインストール

```bash
# macOS
brew install ngrok/ngrok/ngrok

# Linux
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# 認証（https://ngrok.com でアカウント作成後）
ngrok config add-authtoken YOUR_AUTHTOKEN
```

### ステップ2: 依存パッケージのインストール

```bash
cd /home/ubuntu/adinfinitymeta
pip3 install flask requests gspread oauth2client python-dotenv
```

### ステップ3: システムの起動

```bash
./start_with_ngrok.sh
```

画面に表示されるngrokのURL（例: `https://abc123.ngrok.io`）をコピーして、`.env`ファイルに設定：

```bash
# .envファイル
APPROVAL_WEB_URL=https://abc123.ngrok.io
```

## 🎯 使い方

### 1. 停止候補を検出

```bash
python3 meta_abtest_runner.py
```

- 停止候補がSlackに通知されます
- 通知にWeb UIへのリンクが含まれます

### 2. Web UIで承認

- Slackのリンクをクリック
- 承認/却下ボタンをクリック

### 3. 承認済み広告を停止

```bash
python3 approved_stopper.py
```

- 承認済み広告が自動的に停止されます
- Slackに完了通知が送信されます

## 🔄 定期実行（オプション）

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

## 📚 詳細ドキュメント

- **README.md**: システム全体の説明
- **NGROK_SETUP.md**: ngrokの詳細セットアップ
- **CHANGES.md**: 変更内容の詳細
- **SUMMARY.md**: 実装内容のサマリー

## 🆘 困ったら

### Web UIが起動しない
```bash
pip3 install flask
```

### ngrokが見つからない
```bash
which ngrok
# 表示されない場合は再インストール
```

### URLが変わった
```bash
# .envファイルのAPPROVAL_WEB_URLを新しいURLに更新
```

## 🎉 完了！

これで使い始められます。質問があれば各ドキュメントを参照してください。
