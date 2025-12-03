# 広告コピーシステムの使い方

## 📖 概要

インプレッション500以下の広告を自動的に抽出し、新しい広告セット（V2、V3...）にコピーするシステムです。

## 🎯 機能

- ✅ インプレッション500以下の広告を自動抽出
- ✅ V2→V3→V4...と自動増加
- ✅ 広告が3個以下になる場合は広告セット停止
- ✅ コピーした広告は停止状態で作成
- ✅ Slack通知

## 🚀 使い方

### 方法1: GitHub Actionsで実行（推奨）

#### 手動実行

1. https://github.com/kuuhaku1102/adinfinitymeta/actions にアクセス
2. 左側から **「Copy Low Impression Ads」** を選択
3. **「Run workflow」** をクリック
4. **「広告セットID」** を入力
   - 例: `120230617419590484`
5. **「Run workflow」** を再度クリック

#### 自動実行

毎週月曜日午前9時（JST）に自動実行されます。

**注意**: 自動実行するには、GitHub Secretsに `DEFAULT_ADSET_ID` を設定する必要があります。

### 方法2: ローカルで実行

```bash
# リポジトリをクローン
git clone https://github.com/kuuhaku1102/adinfinitymeta.git
cd adinfinitymeta

# 環境変数を設定
export ACCESS_TOKEN="your_meta_access_token"
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_CHANNEL_ID="C01234567890"
export TARGET_ADSET_ID="120230617419590484"

# 実行
python3 ad_copy_low_impression.py
```

## 📋 広告セットIDの確認方法

### Meta広告マネージャーで確認

1. https://business.facebook.com/adsmanager にアクセス
2. 対象の広告セットをクリック
3. URLを確認
   ```
   https://business.facebook.com/adsmanager/manage/adsets?act=...&selected_adset_ids=120230617419590484
                                                                                      ↑ これが広告セットID
   ```

### Meta APIで確認

```bash
curl "https://graph.facebook.com/v19.0/act_YOUR_ACCOUNT_ID/adsets?fields=id,name&access_token=YOUR_ACCESS_TOKEN"
```

## 🔄 処理フロー

```
1. 広告セットIDを指定
   ↓
2. 広告セットから広告を取得
   ↓
3. インプレッション500以下の広告を抽出
   ↓
4. 広告数チェック
   - 4個以上 → 次へ
   - 3個以下 → スキップ（Slack通知）
   ↓
5. コピー後の広告数チェック
   - 4個以上残る → V2作成
   - 3個以下になる → 広告セット停止
   ↓
6. 既存のV2/V3...をチェック
   - V2が存在 → V3を作成
   - V3が存在 → V4を作成
   ↓
7. 新しい広告セットを作成
   ↓
8. 広告をコピー（停止状態）
   ↓
9. Slack通知
```

## 📊 実行例

### 成功例

```
広告セット: 2507-CVCP-segment-Weddings (weddings)
広告数: 10件
インプレッション500以下: 5件
コピー後に残る広告数: 5件

✅ V2広告セット作成: 2507-CVCP-segment-Weddings (weddings)V2
✅ 広告コピー完了: 5件
```

### 広告セット停止例

```
広告セット: 2507-CVCP-segment-Weddings (weddings)
広告数: 10件
インプレッション500以下: 8件
コピー後に残る広告数: 2件

⚠️  コピー後に広告が3個以下になるため、広告セットを停止
✅ 広告セット停止成功
```

### スキップ例

```
広告セット: 2507-CVCP-segment-Weddings (weddings)
広告数: 10件
インプレッション500以下: 2件

⚠️  インプレッション500以下の広告が3個以下のためスキップ
```

## 📱 Slack通知の内容

### 成功時

```
🎉 広告コピー完了

元の広告セット: 2507-CVCP-segment-Weddings (weddings)
新しい広告セット: 2507-CVCP-segment-Weddings (weddings)V2

コピーした広告数: 5件
- 広告A (imp: 300)
- 広告B (imp: 450)
- 広告C (imp: 200)
- 広告D (imp: 350)
- 広告E (imp: 100)

✅ コピーした広告は停止状態で作成されました
```

### 広告セット停止時

```
⚠️  広告セット停止

広告セット: 2507-CVCP-segment-Weddings (weddings)

理由: コピー後に広告が3個以下になるため
元の広告数: 10件
インプレッション500以下: 8件
コピー後に残る広告数: 2件

✅ 広告セットを停止しました
```

## 🔍 パフォーマンス比較

1週間後に自動的にパフォーマンス比較が実行されます。

### 手動実行

```bash
python3 compare_adset_performance.py
```

### GitHub Actionsで実行

1. https://github.com/kuuhaku1102/adinfinitymeta/actions にアクセス
2. 左側から **「Compare AdSet Performance」** を選択
3. **「Run workflow」** をクリック

## ⚙️ 設定

### GitHub Secretsに追加（オプション）

自動実行を有効にする場合：

1. https://github.com/kuuhaku1102/adinfinitymeta/settings/secrets/actions にアクセス
2. **「New repository secret」** をクリック
3. 以下を追加：
   - Name: `DEFAULT_ADSET_ID`
   - Value: `120230617419590484`（デフォルトの広告セットID）

## ❓ トラブルシューティング

### 広告セットIDが見つからない

**エラー**: `広告セット 120230617419590484 が見つかりません`

**解決方法**:
- 広告セットIDが正しいか確認
- 広告セットが削除されていないか確認
- ACCESS_TOKENの権限を確認

### 広告が0件

**エラー**: `インプレッション500以下の広告が0件です`

**解決方法**:
- すべての広告がインプレッション500以上
- 正常な動作です

### V2が既に存在する

**動作**: V3が自動的に作成されます

**確認方法**:
- Slack通知で新しい広告セット名を確認
- Meta広告マネージャーで確認

## 📚 関連ドキュメント

- **AD_COPY_GUIDE.md** - 詳細ガイド
- **SETUP_GUIDE.md** - セットアップ手順
- **README.md** - システム全体の説明
