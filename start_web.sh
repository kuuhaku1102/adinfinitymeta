#!/bin/bash

# Meta広告停止承認システム - Web UI起動スクリプト

echo "🚀 Meta広告停止承認システム Web UIを起動します..."
echo ""

# ディレクトリ移動
cd "$(dirname "$0")"

# 環境変数の確認
if [ ! -f .env ]; then
    echo "⚠️  警告: .envファイルが見つかりません"
    echo "   環境変数を設定してください"
fi

# Flaskの起動
echo "📊 Web UIを起動中..."
echo "   アクセスURL: http://localhost:5000"
echo ""
echo "停止するには Ctrl+C を押してください"
echo ""

python3 approval_web.py
