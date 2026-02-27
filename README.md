# 塾テスト成績トラッカー

NOZOMI GAKUEN 小4 ベーシック講座 成績管理アプリ

## ファイル構成

```
juku_tracker/
├── app.py                  # トップページ
├── data_utils.py           # データ管理ユーティリティ
├── requirements.txt
├── data/
│   └── units.csv           # 単元マスタ（画像から取り込み済み）
└── pages/
    ├── 1_入力.py           # テスト結果入力
    ├── 2_グラフ.py         # 成績グラフ
    ├── 3_単元一覧.py       # 単元一覧
    └── 4_苦手分析.py       # 苦手単元分析
```

## ローカルで動かす

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud にデプロイする手順

1. このフォルダをGitHubリポジトリにpush
2. https://share.streamlit.io にアクセス
3. 「New app」→ リポジトリ・ブランチ・`app.py` を指定してデプロイ

### ⚠️ 注意：Streamlit CloudはCSVデータが永続化されません

テスト結果データ（test_results.csv）はデプロイし直すたびにリセットされます。
将来的にデータを永続化するには **Supabase**（無料PostgreSQL）との連携を推奨します。
その際はdata_utils.pyのload/save関数をSupabaseクライアントに差し替えるだけでOKです。

## 相対スコアについて

標準偏差が入手できない場合、本アプリでは「相対スコア」を使います。

```
相対スコア = (自分の得点率 - 平均得点率) × 100 + 50
```

- 50 = ちょうど平均
- 55 = 平均より5ポイント上
- 45 = 平均より5ポイント下

標準偏差が入手できた場合は、入力フォームの「標準偏差（任意）」に入力すると偏差値も記録されます。
