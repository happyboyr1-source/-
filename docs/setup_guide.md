# セットアップガイド

## 1. 環境構築

### 前提条件
- Python 3.10以上
- pip

### インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd x-affiliate-bot

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 環境変数の設定

```bash
# .env.example をコピー
cp .env.example .env

# .env を編集して各アカウントのAPI情報を入力
```

## 2. X (Twitter) API設定

### Developer Portal でのアプリ作成

1. [X Developer Portal](https://developer.twitter.com/) にアクセス
2. Developer Account を作成（Free Plan）
3. 「Projects & Apps」→「+ Create App」
4. アプリ名を入力（例: `career_shift_bot`）
5. 以下のキーを取得:
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret
   - Bearer Token

### 各アカウントの設定

3アカウント分のアプリを作成する:
- `career_shift_bot` → 転職アカウント用
- `english_hack_bot` → 英会話アカウント用
- `sub_entame_bot` → サブスクアカウント用

取得したキーを `.env` ファイルに記入する。

### API制限（Free Plan）
- **月間500ツイート**（全アカウント合計）
- 3アカウント × 5投稿/日 × 30日 = 450投稿/月（上限内）

## 3. ASP（アフィリエイトサービス）の登録

### A8.net
1. [A8.net](https://www.a8.net/) に会員登録
2. 各プログラムに提携申請:
   - リクルートエージェント
   - doda
   - テックキャンプ
   - U-NEXT
   - DMM TV

### もしもアフィリエイト
1. [もしもアフィリエイト](https://af.moshimo.com/) に会員登録
2. 各プログラムに提携申請:
   - DMM英会話
   - Audible
   - スタディサプリENGLISH

### afb
1. [afb](https://www.afi-b.com/) に会員登録
2. 補助的に使用

## 4. 動作確認

### 設定バリデーション

```bash
python src/bot.py validate
```

### テスト投稿（ドライラン）

```bash
# 1アカウントのテスト
python scripts/test_post.py --account career

# 全アカウントのテスト
python scripts/test_post.py --dry-run
```

### 投稿プレビュー

```bash
# 1日分の投稿をプレビュー
python src/bot.py generate --account career
```

### カレンダー生成

```bash
# 全アカウントの翌月分を生成
python calendar/generate_calendar.py

# 特定アカウント・特定月を生成
python calendar/generate_calendar.py --account career --year 2026 --month 4
```

## 5. 本番運用

### 常駐モードで起動

```bash
# ドライランで動作確認
python scripts/run_all.py --dry-run

# 本番起動
python scripts/run_all.py
```

### cron で定期実行（推奨）

```bash
# crontab に追加
crontab -e

# 15分ごとに実行
*/15 * * * * cd /path/to/project && /path/to/venv/bin/python src/bot.py schedule --due
```

## 6. トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `tweepy.errors.Unauthorized` | API キーが不正 | .env のキーを再確認 |
| `tweepy.errors.TooManyRequests` | レート制限超過 | 自動リトライを待つ |
| 投稿が生成されない | テンプレートファイル不備 | `python src/bot.py validate` で確認 |
| 月間上限到達 | 500投稿に達した | 翌月まで待つ |
