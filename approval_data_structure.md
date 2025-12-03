# 承認データ構造

## pending_approvals.json

停止候補の広告情報を保存するJSONファイル

```json
[
  {
    "ad_id": "120230617419590484",
    "ad_name": "テスト広告A",
    "campaign_name": "春キャンペーン",
    "adset_name": "東京ターゲット",
    "cpa": 1500.50,
    "image_url": "https://example.com/image.jpg",
    "status": "pending",
    "created_at": "2025-12-03T10:30:00",
    "approved_at": null,
    "approved_by": null
  }
]
```

### フィールド説明

- `ad_id`: 広告ID（必須）
- `ad_name`: 広告名
- `campaign_name`: キャンペーン名
- `adset_name`: 広告セット名
- `cpa`: コンバージョン単価（nullの場合もあり）
- `image_url`: 広告画像URL
- `status`: 承認状態
  - `pending`: 承認待ち
  - `approved`: 承認済み
  - `rejected`: 却下
- `created_at`: 停止候補として検出された日時
- `approved_at`: 承認/却下された日時
- `approved_by`: 承認/却下した担当者（将来の拡張用）
