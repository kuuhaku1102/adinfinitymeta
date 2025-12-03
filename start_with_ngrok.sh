#!/bin/bash

# Meta広告停止承認システム - ngrok付き起動スクリプト

echo "🚀 Meta広告停止承認システムをngrokで公開します..."
echo ""

# ディレクトリ移動
cd "$(dirname "$0")"

# 環境変数の確認
if [ ! -f .env ]; then
    echo "⚠️  警告: .envファイルが見つかりません"
    echo "   環境変数を設定してください"
fi

# ngrokがインストールされているか確認
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrokがインストールされていません"
    echo ""
    echo "📥 ngrokのインストール方法:"
    echo "   1. https://ngrok.com/download にアクセス"
    echo "   2. アカウントを作成（無料）"
    echo "   3. ngrokをダウンロードしてインストール"
    echo "   4. ngrok authtoken YOUR_TOKEN で認証"
    echo ""
    exit 1
fi

echo "✅ ngrokが見つかりました"
echo ""

# Flaskを起動（バックグラウンド）
echo "📊 Web UIを起動中..."
python3 approval_web.py > /dev/null 2>&1 &
FLASK_PID=$!

# Flaskの起動を待つ
sleep 3

# ngrokを起動
echo "🌐 ngrokでトンネルを作成中..."
echo ""
ngrok http 5000 &
NGROK_PID=$!

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ システムが起動しました！"
echo ""
echo "📋 次のステップ:"
echo "   1. ngrokの画面に表示されるURL（https://xxxx.ngrok.io）をコピー"
echo "   2. .envファイルのAPPROVAL_WEB_URLにそのURLを設定"
echo "   3. meta_abtest_runner.pyを実行して停止候補を検出"
echo ""
echo "⚠️  注意: ngrokを再起動するとURLが変わります"
echo "   URLが変わったら.envファイルも更新してください"
echo ""
echo "停止するには Ctrl+C を押してください"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 終了シグナルをハンドル
trap "echo ''; echo '🛑 システムを停止中...'; kill $FLASK_PID $NGROK_PID 2>/dev/null; exit" INT TERM

# プロセスが終了するまで待機
wait
