name: Approved Ad Stopper

on:
  workflow_dispatch:  # 手動実行を許可

jobs:
  stop-approved:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Reconstruct credentials.json
        run: echo "${{ secrets.GSHEET_JSON }}" | base64 -d > credentials.json

      - name: Run approved stopper script
        run: python approved_stopper.py
        env:
          ACCESS_TOKEN: ${{ secrets.META_ACCESS_TOKEN }}
          SPREADSHEET_URL: ${{ secrets.SPREADSHEET_URL }}
