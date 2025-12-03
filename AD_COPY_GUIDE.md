# 広告コピー機能ガイド

インプレッション500以下の広告を自動でコピーし、V2広告セットを作成する機能です。

## 📋 機能概要

### 処理フロー

1. **広告セットから広告を取得**
   - 指定した広告セット内の全広告を取得
   - 過去14日間のインプレッション数を確認

2. **インプレッション500以下の広告を抽出**
   - 閾値以下の広告をリストアップ

3. **広告数チェック**
   - 抽出した広告が **4個以上** → V2広告セット作成
   - 抽出した広告が **3個以下** → スキップ
   - コピー後に元の広告セットの広告が **3個以下** → 広告セット停止

4. **V2広告セットを自動作成**
   - 名前: 元の名前 + `V2`
   - 設定: 元の広告セットと同じ（ターゲティング、予算、入札戦略）

5. **広告をコピー**
   - 抽出した広告をV2広告セットにコピー
   - **コピーした広告は停止状態**
   - 元の広告は配信継続

6. **Slack通知**
   - コピー完了通知
   - または広告セット停止通知

## 🚀 使い方

### 1. 広告コピーの実行

```bash
# 広告セットIDを指定して実行
TARGET_ADSET_ID=123456789 python3 ad_copy_low_impression.py
```

### 2. パフォーマンス比較（1週間後）

```bash
# 自動的に最新のコピー履歴を取得して比較
python3 compare_adset_performance.py
```

## 📊 パフォーマンス比較

1週間後に実行すると、以下の指標を比較：

- **インプレッション数**
- **支出額**
- **クリック数**
- **CTR（クリック率）**
- **CPA（コンバージョン単価）**

優勝者（CPAが低い方）を自動判定してSlackに通知します。

## 🔧 設定

### 環境変数

`.env`ファイルに以下を設定：

```bash
# Meta広告API
ACCESS_TOKEN=your_meta_access_token

# Slack通知
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=C01234567890
```

### カスタマイズ

`ad_copy_low_impression.py`の設定を変更できます：

```python
IMPRESSION_THRESHOLD = 500  # インプレッション閾値
MIN_AD_COUNT = 4           # 最小広告数
DATE_RANGE_DAYS = 14       # データ取得期間（日）
```

## 📝 コピー履歴

`ad_copy_history.json`にコピー履歴が記録されます：

```json
[
  {
    "timestamp": "2025-01-15T10:30:00",
    "original_adset_id": "123456789",
    "original_adset_name": "2507-CVCP-segment-Weddings (weddings)",
    "v2_adset_id": "987654321",
    "v2_adset_name": "2507-CVCP-segment-Weddings (weddings)V2",
    "copied_ads": [
      {
        "original_id": "111111",
        "new_id": "222222",
        "name": "広告A",
        "impressions": 300
      }
    ]
  }
]
```

## ⚙️ GitHub Actionsでの自動実行

### 週1回実行する場合

`.github/workflows/ad_copy_weekly.yml`を作成：

```yaml
name: Weekly Ad Copy

on:
  schedule:
    - cron: '0 9 * * 1'  # 毎週月曜日 9:00 JST
  workflow_dispatch:

jobs:
  copy-ads:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install requests python-dotenv
      
      - name: Create .env file
        run: |
          cat << EOF > .env
          ACCESS_TOKEN=${{ secrets.META_ACCESS_TOKEN }}
          SLACK_BOT_TOKEN=${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_CHANNEL_ID=${{ secrets.SLACK_CHANNEL_ID }}
          EOF
      
      - name: Run ad copy
        run: |
          TARGET_ADSET_ID=${{ secrets.TARGET_ADSET_ID }} python3 ad_copy_low_impression.py
```

## 🎯 実行例

### 成功例

```
広告セット処理開始: 123456789
広告セット名: 2507-CVCP-segment-Weddings (weddings)
広告数: 10件

広告のインサイトを取得中...
  - 広告A: 300 imp
  - 広告B: 800 imp
  - 広告C: 450 imp
  - 広告D: 600 imp
  - 広告E: 250 imp
  ...

インプレッション500以下の広告: 5件
コピー後に残る広告数: 5件

V2広告セットを作成中...
✅ V2広告セット作成成功: 2507-CVCP-segment-Weddings (weddings)V2

広告をコピー中...
  ✅ 広告コピー成功: 広告A → 新ID: 222222
  ✅ 広告コピー成功: 広告C → 新ID: 333333
  ✅ 広告コピー成功: 広告E → 新ID: 444444
  ...

✅ 広告コピー完了
```

### スキップ例（広告数不足）

```
インプレッション500以下の広告: 2件

⚠️  広告数が4個未満のためスキップ

広告セット: 2507-CVCP-segment-Weddings (weddings)
対象広告数: 2件
```

### 広告セット停止例

```
インプレッション500以下の広告: 8件
コピー後に残る広告数: 2件

⚠️  コピー後に広告が3個以下になるため、元の広告セットを停止します
✅ 広告セット停止成功: 2507-CVCP-segment-Weddings (weddings)
```

## 🔍 トラブルシューティング

### エラー: ACCESS_TOKENが未設定

`.env`ファイルに`ACCESS_TOKEN`を設定してください。

### エラー: TARGET_ADSET_IDが未設定

実行時に広告セットIDを指定してください：

```bash
TARGET_ADSET_ID=123456789 python3 ad_copy_low_impression.py
```

### エラー: 広告セット作成失敗

- Meta APIの権限を確認
- 広告セットの設定が正しいか確認
- 予算設定が適切か確認

## 📚 関連ファイル

- `ad_copy_low_impression.py` - 広告コピースクリプト
- `compare_adset_performance.py` - パフォーマンス比較スクリプト
- `ad_copy_history.json` - コピー履歴
- `AD_COPY_GUIDE.md` - このドキュメント
