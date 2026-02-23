# X (Twitter) API 設定手順

## 1. Developer Account の作成

1. [developer.twitter.com](https://developer.twitter.com/) にアクセス
2. 「Sign up」をクリック
3. X アカウントでログイン
4. 利用目的を選択（「Making a bot」等）
5. 規約に同意して登録完了

## 2. Free Plan の確認

Free Plan では以下が利用可能:
- **月間1,500ツイート読み取り**
- **月間500ツイート投稿**
- 1つの環境（Development）
- OAuth 2.0 / OAuth 1.0a 対応

## 3. App の作成

### 手順

1. Developer Portal の「Projects & Apps」にアクセス
2. 「+ Add App」をクリック
3. アプリ名を入力
4. 「App permissions」を **Read and Write** に設定
5. 「Keys and tokens」タブから以下を取得:

### 取得するキー

| キー名 | 説明 | .env の変数名（転職） |
|--------|------|---------------------|
| API Key | Consumer Key | CAREER_API_KEY |
| API Key Secret | Consumer Secret | CAREER_API_SECRET |
| Access Token | ユーザー認証トークン | CAREER_ACCESS_TOKEN |
| Access Token Secret | ユーザー認証シークレット | CAREER_ACCESS_TOKEN_SECRET |
| Bearer Token | App-only 認証用 | CAREER_BEARER_TOKEN |

## 4. OAuth 1.0a User Context の設定

Bot が各アカウントとして投稿するには、**OAuth 1.0a User Context** が必要。

1. 各 X アカウントでログイン
2. Developer Portal でそのアカウントの App を作成
3. Access Token と Access Token Secret を「Regenerate」で生成
4. **この時点でトークンは1回しか表示されない** ので必ずコピーする

## 5. 3アカウント分の設定

各アカウントごとに独立した App を作成する:

```
転職アカウント (@career_shift_lab)
├── App名: career_shift_bot
├── API Key → CAREER_API_KEY
├── API Secret → CAREER_API_SECRET
├── Access Token → CAREER_ACCESS_TOKEN
└── Access Token Secret → CAREER_ACCESS_TOKEN_SECRET

英会話アカウント (@english_hack_jp)
├── App名: english_hack_bot
├── API Key → ENGLISH_API_KEY
├── API Secret → ENGLISH_API_SECRET
├── Access Token → ENGLISH_ACCESS_TOKEN
└── Access Token Secret → ENGLISH_ACCESS_TOKEN_SECRET

サブスクアカウント (@sub_entame_navi)
├── App名: sub_entame_bot
├── API Key → SUBSCRIP_API_KEY
├── API Secret → SUBSCRIP_API_SECRET
├── Access Token → SUBSCRIP_ACCESS_TOKEN
└── Access Token Secret → SUBSCRIP_ACCESS_TOKEN_SECRET
```

## 6. 動作テスト

```bash
# 環境変数が正しく設定されているか確認
python -c "from src.config_loader import load_account_config, get_credentials; \
  c = load_account_config('career'); \
  creds = get_credentials(c); \
  print('OK' if all(creds.values()) else 'NG: 未設定の環境変数があります')"
```

## 7. 注意事項

- **トークンは絶対に公開しない**（.env は .gitignore に含まれている）
- Free Plan の月間500投稿制限を超えないよう注意
- 各アカウントの App permissions は必ず「Read and Write」に設定
- トークンを再生成すると古いトークンは無効になる
