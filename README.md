# X (Twitter) アフィリエイト自動化Bot

月10万円/アカウントを目標とした、3つのXアカウントの自動投稿システム。

## 3アカウント構成

| アカウント | ジャンル | 主要ASP案件 | 収益モデル |
|-----------|---------|------------|-----------|
| @career_shift_lab | 転職・キャリア | 転職エージェント登録 (1-3万/件) | 高単価×少量 |
| @english_hack_jp | オンライン英会話 | 英会話無料体験 (3-4千/件) | 中単価×中量 |
| @sub_entame_navi | サブスク・VOD | VOD無料トライアル (1.5-3千/件) | 低単価×大量 |

## 機能

- **テンプレートベース投稿生成**: Jinja2テンプレートによる自然な投稿文生成
- **自動スケジューリング**: APSchedulerによるJST対応の定時投稿
- **ステマ規制準拠**: #PR表記の自動チェック・バリデーション
- **レート制限管理**: X API Free Plan (500投稿/月) の自動管理
- **1ヶ月カレンダー生成**: 30日分 × 5投稿/日 = 150投稿を事前生成
- **ドライランモード**: API呼び出しなしのテスト実行

## クイックスタート

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .env にAPI Keyを入力

# 設定バリデーション
python src/bot.py validate

# テスト投稿（ドライラン）
python scripts/test_post.py --dry-run

# 投稿プレビュー
python src/bot.py generate --account career

# カレンダー生成
python calendar/generate_calendar.py

# Bot起動（ドライラン）
python scripts/run_all.py --dry-run
```

## プロジェクト構成

```
├── config/              # アカウント設定 (YAML)
├── src/                 # メインソースコード
│   ├── bot.py           # CLI エントリポイント
│   ├── poster.py        # X API投稿 (tweepy v2)
│   ├── scheduler.py     # APScheduler スケジューラー
│   ├── content_generator.py  # テンプレート投稿生成
│   ├── config_loader.py # 設定読み込み
│   └── compliance.py    # ステマ規制チェック
├── templates/           # 投稿テンプレート (YAML)
│   ├── career/          # 転職系
│   ├── english/         # 英会話系
│   └── subscrip/        # サブスク系
├── calendar/            # カレンダー生成
├── scripts/             # 運用スクリプト
├── docs/                # ドキュメント
└── roadmap/             # 6ヶ月収益化ロードマップ
```

## 投稿スケジュール

- **5投稿/日/アカウント** × 3アカウント = 15投稿/日
- ゴールデンタイム: 7:00, 8:30, 12:00, 18:00, 21:00 JST
- 週間テーマローテーション（Tips/エンゲージメント/アフィリエイト）
- アフィリエイト比率: 約11%（自然な比率を維持）

## 必要な事前準備

1. X Developer Portal でAPI Key取得（3アカウント分）
2. ASP（A8.net、もしもアフィリエイト等）の会員登録とプログラム提携
3. ブログ/LPの作成（アフィリエイトリンク設置先）

詳細は [docs/setup_guide.md](docs/setup_guide.md) を参照。
