# 本番デプロイガイド

## デプロイ方法の選択

| 方法 | 推奨環境 | コスト目安 | 難易度 |
|------|---------|-----------|--------|
| Docker Compose | VPS / クラウドVM | 月額500-1,000円 | 低 |
| systemd (常駐) | VPS / 自宅サーバー | 月額500-1,000円 | 中 |
| systemd timer (cron式) | VPS / 自宅サーバー | 月額500-1,000円 | 中 |

---

## 方法1: Docker Compose（推奨）

### 前提条件
- Docker Engine 20.10+
- Docker Compose V2

### 手順

```bash
# 1. リポジトリをクローン
git clone <repository-url> /opt/x-affiliate-bot
cd /opt/x-affiliate-bot

# 2. 環境変数を設定
cp .env.example .env
# .env を編集して API キーと通知設定を入力

# 3. ビルド＆起動
docker compose up -d

# 4. ログ確認
docker compose logs -f

# 5. ヘルスチェック
docker compose exec bot python src/bot.py health

# 6. 停止
docker compose down
```

### 運用コマンド

```bash
# ステータス確認
docker compose exec bot python src/bot.py status

# 投稿分析レポート
docker compose exec bot python src/bot.py report

# 設定変更後の再起動
docker compose restart

# イメージ更新
git pull
docker compose up -d --build
```

---

## 方法2: systemd 常駐モード

### 手順

```bash
# 1. アプリケーションの配置
sudo mkdir -p /opt/x-affiliate-bot
sudo cp -r . /opt/x-affiliate-bot/
cd /opt/x-affiliate-bot

# 2. 実行ユーザー作成
sudo useradd -r -s /bin/false bot

# 3. 仮想環境の作成
sudo -u bot python3 -m venv venv
sudo -u bot venv/bin/pip install -r requirements.txt

# 4. 環境変数を設定
sudo cp .env.example .env
sudo chmod 600 .env
# .env を編集

# 5. ディレクトリ権限
sudo chown -R bot:bot /opt/x-affiliate-bot
sudo mkdir -p /opt/x-affiliate-bot/{data,logs}
sudo chown bot:bot /opt/x-affiliate-bot/{data,logs}

# 6. サービスファイルの配置
sudo cp deploy/x-affiliate-bot.service /etc/systemd/system/

# 7. 起動
sudo systemctl daemon-reload
sudo systemctl enable x-affiliate-bot
sudo systemctl start x-affiliate-bot

# 8. ステータス確認
sudo systemctl status x-affiliate-bot
sudo journalctl -u x-affiliate-bot -f
```

---

## 方法3: systemd timer（cron式）

15分間隔で投稿チェックを行う方法。常駐しないためリソース消費が少ない。

```bash
# 1-5は方法2と同じ

# 6. サービス＆タイマーの配置
sudo cp deploy/x-affiliate-bot-cron.service /etc/systemd/system/
sudo cp deploy/x-affiliate-bot-cron.timer /etc/systemd/system/

# 7. タイマー起動
sudo systemctl daemon-reload
sudo systemctl enable x-affiliate-bot-cron.timer
sudo systemctl start x-affiliate-bot-cron.timer

# 8. タイマー状態確認
sudo systemctl list-timers | grep x-affiliate
```

---

## 通知設定

投稿失敗やシステムイベントを通知するため、以下のいずれかを `.env` に設定してください。

### Discord

1. Discordサーバーの設定 → 連携サービス → Webhook → 新しいWebhook
2. WebhookのURLをコピー

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxx/yyyy
```

### LINE Notify

1. https://notify-bot.line.me/ でトークンを発行
2. 通知先のグループを選択

```bash
LINE_NOTIFY_TOKEN=your_line_notify_token
```

### Slack

1. Slack App → Incoming Webhooks → Webhook URLを取得

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
```

### 通知されるイベント

| イベント | レベル | 内容 |
|---------|--------|------|
| Bot起動 | INFO | 起動モード（LIVE/DRY RUN） |
| 投稿失敗 | ERROR | アカウント名とエラー詳細 |
| レート制限警告 | WARNING | 月間残り投稿数 |
| 日次レポート | INFO/WARNING | 成功/失敗件数 |

---

## 運用チェックリスト

### 起動前の確認

```bash
# 設定バリデーション
python src/bot.py validate

# ヘルスチェック
python src/bot.py health

# ドライランテスト
python scripts/test_post.py --dry-run

# 1件のライブテスト（任意）
python scripts/test_post.py --account career --live
```

### 日常の監視

```bash
# ステータス確認
python src/bot.py status

# 投稿分析レポート
python src/bot.py report

# ログ確認
tail -f logs/bot.log

# エラーログ確認
tail -f logs/error.log
```

### 月次作業

1. 翌月のカレンダー生成（オプション）:
   ```bash
   python calendar/generate_calendar.py --month <次月>
   ```
2. レート制限のリセット確認（月初に自動リセット）
3. テンプレートの追加・改善
4. ASP管理画面でコンバージョン確認

---

## ログ構成

| ファイル | 内容 | ローテーション |
|---------|------|---------------|
| `logs/bot.log` | 全ログ | 5MB × 5世代 |
| `logs/error.log` | エラーのみ | 5MB × 5世代 |
| `data/analytics/YYYY-MM-DD.jsonl` | 投稿記録 | 日次ファイル |
| `data/rate_limits.json` | レート制限カウンター | 月次リセット |

---

## トラブルシューティング

| 症状 | 確認コマンド | 対処 |
|------|------------|------|
| Bot が起動しない | `python src/bot.py health` | ヘルスチェックのFAIL項目を修正 |
| 投稿が実行されない | `python src/bot.py status` | レート制限と投稿時間を確認 |
| 通知が来ない | `logs/bot.log` で通知ログ確認 | Webhook URLの設定を確認 |
| API認証エラー | `logs/error.log` | `.env` のキーを再確認 |
| Dockerが落ちる | `docker compose logs` | メモリ不足がないか確認 |
