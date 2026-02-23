"""YAML設定ファイルの読み込み・バリデーション・アカウント管理"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_env():
    """環境変数を .env ファイルから読み込む"""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def load_yaml(filepath):
    """YAMLファイルを読み込んで辞書として返す"""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_accounts_config():
    """accounts.yaml を読み込んで全アカウント情報を返す"""
    return load_yaml(CONFIG_DIR / "accounts.yaml")


def load_account_config(account_id):
    """指定されたアカウントIDの詳細設定を読み込む

    Args:
        account_id: "career", "english", "subscrip" のいずれか

    Returns:
        dict: アカウントの詳細設定
    """
    accounts = load_accounts_config()
    account_entry = None
    for acc in accounts["accounts"]:
        if acc["id"] == account_id:
            account_entry = acc
            break

    if account_entry is None:
        raise ValueError(f"アカウント '{account_id}' が見つかりません")

    config_file = CONFIG_DIR / account_entry["config_file"]
    if not config_file.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_file}")

    return load_yaml(config_file)


def get_credentials(account_config):
    """アカウント設定から環境変数を解決してAPI認証情報を返す

    Args:
        account_config: load_account_config() の戻り値

    Returns:
        dict: api_key, api_secret, access_token, access_token_secret, bearer_token
    """
    load_env()
    creds_env = account_config["credentials_env"]
    credentials = {}
    for key, env_var in creds_env.items():
        value = os.getenv(env_var, "")
        if not value:
            print(f"  警告: 環境変数 {env_var} が設定されていません")
        credentials[key] = value
    return credentials


def get_all_account_ids():
    """有効な全アカウントIDのリストを返す"""
    accounts = load_accounts_config()
    return [acc["id"] for acc in accounts["accounts"] if acc.get("enabled", True)]


def validate_account_config(account_config):
    """アカウント設定のバリデーションを行う

    Returns:
        list: エラーメッセージのリスト（空なら正常）
    """
    errors = []

    # 必須フィールドチェック
    required_fields = ["account", "credentials_env", "voice", "content_strategy",
                       "affiliate", "compliance", "posting_times_jst"]
    for field in required_fields:
        if field not in account_config:
            errors.append(f"必須フィールド '{field}' がありません")

    # content_mix の合計チェック
    if "content_strategy" in account_config:
        mix = account_config["content_strategy"].get("content_mix", {})
        total = sum(mix.values())
        if abs(total - 1.0) > 0.01:
            errors.append(f"content_mix の合計が1.0ではありません: {total}")

    # 投稿時間数のチェック
    times = account_config.get("posting_times_jst", [])
    posts_per_day = account_config.get("content_strategy", {}).get("posts_per_day", 5)
    if len(times) != posts_per_day:
        errors.append(
            f"posting_times_jst ({len(times)}個) と "
            f"posts_per_day ({posts_per_day}) が一致しません"
        )

    # コンプライアンス設定チェック
    compliance = account_config.get("compliance", {})
    if compliance.get("pr_label_format") != "#PR":
        errors.append("PR表記は '#PR' を使用してください")

    return errors


def validate_all_configs():
    """全アカウントの設定をバリデーションする

    Returns:
        dict: {account_id: [error_messages]}
    """
    results = {}
    for account_id in get_all_account_ids():
        try:
            config = load_account_config(account_id)
            errors = validate_account_config(config)
            results[account_id] = errors
        except Exception as e:
            results[account_id] = [str(e)]
    return results
