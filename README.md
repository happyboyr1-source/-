# YouTubeコミュニティ投稿いいね比較ツール

指定した複数のYouTubeコミュニティ投稿のいいね数を取得し、いいね数が多い順に並べて毎日通知するためのツールです。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 設定ファイル

`config.yaml` を作成します。

```yaml
posts:
  - "https://www.youtube.com/post/Ugkx..."
  - "https://www.youtube.com/post/Ugkx..."
notify:
  method: "stdout" # stdout or slack
  # slack:
  #   webhook_url: "https://hooks.slack.com/services/..."
```

`config.example.yaml` をコピーして利用することもできます。

## 実行

1回だけ実行:

```bash
yt-community-likes --config config.yaml run
```

毎日実行 (09:00に通知):

```bash
yt-community-likes --config config.yaml schedule --time 09:00
```

## 通知先

- `stdout`: 標準出力に通知を表示します。
- `slack`: Incoming Webhookを使ってSlackへ通知します。

## メモ

- YouTubeのHTMLを解析していいね数を取得します。ページ構造の変更で取得できなくなる場合があります。
