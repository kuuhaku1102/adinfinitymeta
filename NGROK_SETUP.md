# ngrokを使った公開セットアップガイド

ngrokを使うと、**サーバー不要**で外部からWeb UIにアクセスできるようになります。

## 🎯 ngrokとは？

- **無料**で使えるトンネリングサービス
- ローカルで動いているWebアプリを一時的に公開できる
- HTTPSに対応（セキュアな接続）
- URLは毎回変わる（有料プランで固定可能）

## 📥 ngrokのインストール

### 1. ngrokアカウントの作成

1. https://ngrok.com/ にアクセス
2. 「Sign up」をクリックして無料アカウントを作成
3. ログイン後、ダッシュボードで「Authtoken」を確認

### 2. ngrokのインストール

#### macOS (Homebrew)
```bash
brew install ngrok/ngrok/ngrok
```

#### Linux
```bash
# ダウンロード
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# または直接ダウンロード
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
```

#### Windows
1. https://ngrok.com/download からダウンロード
2. ZIPを解凍
3. `ngrok.exe`をPATHに追加

### 3. ngrokの認証

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
```

**YOUR_AUTHTOKEN**は、ngrokのダッシュボードで確認できます。

## 🚀 起動方法

### 方法1: 自動起動スクリプト（おすすめ）

```bash
cd /home/ubuntu/adinfinitymeta
./start_with_ngrok.sh
```

このスクリプトは以下を自動で行います：
- Flask Web UIの起動
- ngrokトンネルの作成
- 公開URLの表示

### 方法2: 手動起動

#### ステップ1: Web UIを起動

```bash
cd /home/ubuntu/adinfinitymeta
python3 approval_web.py
```

#### ステップ2: 別のターミナルでngrokを起動

```bash
ngrok http 5000
```

## 📋 使い方

### 1. ngrokのURLを確認

ngrokを起動すると、以下のような画面が表示されます：

```
ngrok

Session Status                online
Account                       your-email@example.com
Version                       3.x.x
Region                        Japan (jp)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:5000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**重要**: `Forwarding`の行にある`https://abc123.ngrok.io`があなたの公開URLです。

### 2. 環境変数に設定

`.env`ファイルを編集して、ngrokのURLを設定します：

```bash
# .envファイル
APPROVAL_WEB_URL=https://abc123.ngrok.io
```

### 3. 停止候補を検出

```bash
python3 meta_abtest_runner.py
```

Slack通知に、ngrokのURLが含まれます。

### 4. Web UIで承認

Slackの通知からリンクをクリックすると、Web UIが開きます。
承認/却下ボタンをクリックして操作します。

### 5. 承認済み広告を停止

```bash
python3 approved_stopper.py
```

## 🔄 URLが変わったら

ngrokを再起動すると、URLが変わります。その場合：

1. 新しいngrokのURLを確認
2. `.env`ファイルの`APPROVAL_WEB_URL`を更新
3. `meta_abtest_runner.py`を再実行

## 💡 便利な機能

### ngrok Web Interface

ngrokを起動すると、`http://127.0.0.1:4040`でWeb Interfaceが利用できます。

**できること**：
- リクエスト履歴の確認
- リクエスト/レスポンスの詳細表示
- リプレイ機能

### トンネルの状態確認

```bash
curl http://127.0.0.1:4040/api/tunnels
```

## 🔒 セキュリティ

### Basic認証の追加（推奨）

ngrokに認証を追加できます：

```bash
ngrok http 5000 --basic-auth="username:password"
```

または、起動スクリプトを編集：

```bash
# start_with_ngrok.sh の ngrok 起動部分を変更
ngrok http 5000 --basic-auth="admin:your-password" &
```

### IPアドレス制限

有料プランでは、特定のIPアドレスからのみアクセスを許可できます。

## 💰 有料プラン（オプション）

### 無料プラン
- ✅ HTTPS対応
- ✅ 基本的な機能
- ❌ URLが毎回変わる
- ❌ 同時接続数制限

### 有料プラン（$8/月〜）
- ✅ 固定URL（カスタムドメイン）
- ✅ 同時接続数増加
- ✅ IPアドレス制限
- ✅ より高速

詳細: https://ngrok.com/pricing

## 🐛 トラブルシューティング

### ngrokが起動しない

```bash
# ngrokのバージョン確認
ngrok version

# 認証トークンの再設定
ngrok config add-authtoken YOUR_AUTHTOKEN
```

### URLにアクセスできない

1. Flaskが起動しているか確認
   ```bash
   curl http://localhost:5000
   ```

2. ngrokのトンネルが作成されているか確認
   ```bash
   curl http://127.0.0.1:4040/api/tunnels
   ```

3. ファイアウォールの確認

### "ERR_NGROK_108" エラー

無料プランでは、1つのngrokトンネルしか同時に起動できません。
既存のngrokプロセスを終了してください：

```bash
pkill ngrok
```

## 📝 注意事項

1. **URLは毎回変わる**
   - ngrokを再起動するたびにURLが変わります
   - `.env`ファイルの更新を忘れずに

2. **無料プランの制限**
   - 同時接続数に制限があります
   - 長時間の接続には向きません

3. **セキュリティ**
   - 公開URLは誰でもアクセス可能
   - Basic認証の追加を推奨
   - 機密情報を扱う場合は有料プランを検討

4. **本番運用**
   - テストや一時的な利用に適しています
   - 本格的な運用には専用サーバーを推奨

## 🎉 完了！

これでngrokを使った公開が可能になりました。
質問があれば、README.mdも参照してください。
