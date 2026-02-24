"""X (Twitter) API v2 投稿モジュール

tweepy.Client を使用してツイートを投稿する。
各アカウントごとに独立したクライアントを生成し、
レート制限とリトライを管理する。
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import tweepy

from src.config_loader import get_credentials
from src.logger import get_logger


logger = get_logger(__name__)

# レート制限追跡ファイル
RATE_LIMIT_FILE = Path(__file__).parent.parent / "data" / "rate_limits.json"

# 月間投稿上限（X API Free Plan）
MONTHLY_POST_LIMIT = 500

# リトライ設定
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # 秒


def create_client(account_config):
    """アカウント設定からtweepy.Clientを生成する

    Args:
        account_config: アカウントの詳細設定辞書

    Returns:
        tweepy.Client: 認証済みクライアント
    """
    creds = get_credentials(account_config)
    client = tweepy.Client(
        consumer_key=creds["api_key"],
        consumer_secret=creds["api_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_token_secret"],
    )
    return client


def _load_rate_limits():
    """レート制限カウンターを読み込む"""
    if RATE_LIMIT_FILE.exists():
        with open(RATE_LIMIT_FILE, "r") as f:
            return json.load(f)
    return {"monthly_count": 0, "month": None, "daily_counts": {}}


def _save_rate_limits(data):
    """レート制限カウンターを保存する"""
    RATE_LIMIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RATE_LIMIT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def check_rate_limit():
    """レート制限をチェックする

    Returns:
        tuple: (can_post, remaining_count, error_message or None)
    """
    limits = _load_rate_limits()
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 月が変わったらリセット
    if limits.get("month") != current_month:
        limits = {"monthly_count": 0, "month": current_month, "daily_counts": {}}
        _save_rate_limits(limits)

    remaining = MONTHLY_POST_LIMIT - limits["monthly_count"]

    if remaining <= 0:
        return False, 0, "月間投稿上限（500件）に達しました"

    # 1日あたりの安全上限チェック（17件/日）
    daily_count = limits["daily_counts"].get(today, 0)
    if daily_count >= 17:
        return False, remaining, "本日の投稿上限（17件）に達しました"

    return True, remaining, None


def _increment_rate_limit():
    """投稿カウンターをインクリメントする"""
    limits = _load_rate_limits()
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if limits.get("month") != current_month:
        limits = {"monthly_count": 0, "month": current_month, "daily_counts": {}}

    limits["monthly_count"] += 1
    limits["daily_counts"][today] = limits["daily_counts"].get(today, 0) + 1
    _save_rate_limits(limits)


def post_tweet(account_config, text, dry_run=False):
    """ツイートを1件投稿する

    Args:
        account_config: アカウントの詳細設定
        text: 投稿テキスト
        dry_run: Trueの場合、APIを呼ばずにシミュレーションする

    Returns:
        dict: {
            "success": bool,
            "tweet_id": str or None,
            "error": str or None,
            "dry_run": bool
        }
    """
    account_name = account_config["account"]["display_name"]

    # レート制限チェック
    can_post, remaining, limit_error = check_rate_limit()
    if not can_post:
        logger.warning("[%s] レート制限: %s", account_name, limit_error)
        return {
            "success": False,
            "tweet_id": None,
            "error": limit_error,
            "dry_run": dry_run,
        }

    if dry_run:
        logger.info("[DRY RUN] [%s] %s...", account_name, text[:60])
        return {
            "success": True,
            "tweet_id": "dry_run_id",
            "error": None,
            "dry_run": True,
        }

    # リトライ付きAPI呼び出し
    client = create_client(account_config)
    for attempt in range(MAX_RETRIES):
        try:
            response = client.create_tweet(text=text)
            _increment_rate_limit()
            tweet_id = response.data["id"]
            logger.info("[POSTED] [%s] ID:%s - %s...", account_name, tweet_id, text[:40])
            return {
                "success": True,
                "tweet_id": str(tweet_id),
                "error": None,
                "dry_run": False,
            }
        except tweepy.TooManyRequests:
            wait_time = RETRY_BASE_DELAY * (2 ** attempt)
            logger.warning(
                "[RATE LIMIT] [%s] %d秒後にリトライ (%d/%d)",
                account_name, wait_time, attempt + 1, MAX_RETRIES,
            )
            time.sleep(wait_time)
        except tweepy.TweepyException as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "[ERROR] [%s] %s - %d秒後にリトライ (%d/%d)",
                    account_name, e, wait_time, attempt + 1, MAX_RETRIES,
                )
                time.sleep(wait_time)
            else:
                logger.error("[FAIL] [%s] 投稿失敗: %s", account_name, e)
                return {
                    "success": False,
                    "tweet_id": None,
                    "error": str(e),
                    "dry_run": False,
                }

    logger.error("[FAIL] [%s] 最大リトライ回数超過", account_name)
    return {
        "success": False,
        "tweet_id": None,
        "error": "最大リトライ回数を超えました",
        "dry_run": False,
    }


def post_thread(account_config, texts, dry_run=False):
    """スレッド（連続ツイート）を投稿する

    Args:
        account_config: アカウントの詳細設定
        texts: 投稿テキストのリスト（先頭がスレッド開始）
        dry_run: Trueの場合シミュレーション

    Returns:
        list[dict]: 各ツイートの投稿結果リスト
    """
    account_name = account_config["account"]["display_name"]
    results = []
    previous_tweet_id = None

    for i, text in enumerate(texts):
        if dry_run:
            result = post_tweet(account_config, text, dry_run=True)
            results.append(result)
            continue

        # レート制限チェック
        can_post, _, limit_error = check_rate_limit()
        if not can_post:
            logger.warning("[%s] スレッド中断 (%d/%d): %s", account_name, i + 1, len(texts), limit_error)
            results.append({
                "success": False,
                "tweet_id": None,
                "error": limit_error,
                "dry_run": False,
            })
            break

        client = create_client(account_config)
        try:
            kwargs = {"text": text}
            if previous_tweet_id:
                kwargs["in_reply_to_tweet_id"] = previous_tweet_id

            response = client.create_tweet(**kwargs)
            _increment_rate_limit()
            tweet_id = str(response.data["id"])
            previous_tweet_id = tweet_id
            results.append({
                "success": True,
                "tweet_id": tweet_id,
                "error": None,
                "dry_run": False,
            })
        except tweepy.TweepyException as e:
            logger.error("[%s] スレッド投稿失敗 (%d/%d): %s", account_name, i + 1, len(texts), e)
            results.append({
                "success": False,
                "tweet_id": None,
                "error": str(e),
                "dry_run": False,
            })
            break  # スレッドの途中で失敗したら中断

    return results
