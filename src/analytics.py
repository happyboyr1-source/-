"""投稿パフォーマンス分析・トラッキングモジュール

各投稿の結果をJSONログとして記録し、
日次・月次のサマリーレポートを生成する。
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.logger import get_logger


logger = get_logger(__name__)

JST = timezone(timedelta(hours=9))
ANALYTICS_DIR = Path(__file__).parent.parent / "data" / "analytics"


def _ensure_dir():
    """分析データディレクトリを作成する"""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


def record_post(account_id, content_type, text, result, dry_run=False):
    """投稿結果を記録する

    Args:
        account_id: アカウントID
        content_type: コンテンツタイプ
        text: 投稿テキスト
        result: post_tweet()の戻り値
        dry_run: ドライランフラグ
    """
    if dry_run:
        return

    _ensure_dir()
    now = datetime.now(JST)
    date_str = now.strftime("%Y-%m-%d")

    record = {
        "timestamp": now.isoformat(),
        "account_id": account_id,
        "content_type": content_type,
        "text_preview": text[:80],
        "char_count": len(text),
        "success": result["success"],
        "tweet_id": result.get("tweet_id"),
        "error": result.get("error"),
    }

    # 日次ファイルに追記
    log_file = ANALYTICS_DIR / f"{date_str}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_daily_summary(date_str=None):
    """日次サマリーを取得する

    Args:
        date_str: "YYYY-MM-DD"形式（Noneなら今日）

    Returns:
        dict: {
            "date": str,
            "total": int,
            "success": int,
            "failed": int,
            "by_account": {account_id: {success: int, failed: int}},
            "by_type": {content_type: int}
        }
    """
    if date_str is None:
        date_str = datetime.now(JST).strftime("%Y-%m-%d")

    log_file = ANALYTICS_DIR / f"{date_str}.jsonl"

    summary = {
        "date": date_str,
        "total": 0,
        "success": 0,
        "failed": 0,
        "by_account": {},
        "by_type": {},
    }

    if not log_file.exists():
        return summary

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            summary["total"] += 1

            if record["success"]:
                summary["success"] += 1
            else:
                summary["failed"] += 1

            # アカウント別
            acc = record["account_id"]
            if acc not in summary["by_account"]:
                summary["by_account"][acc] = {"success": 0, "failed": 0}
            if record["success"]:
                summary["by_account"][acc]["success"] += 1
            else:
                summary["by_account"][acc]["failed"] += 1

            # タイプ別
            ct = record["content_type"]
            summary["by_type"][ct] = summary["by_type"].get(ct, 0) + 1

    return summary


def get_monthly_summary(year=None, month=None):
    """月次サマリーを取得する

    Returns:
        dict: 月全体の集計結果
    """
    now = datetime.now(JST)
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    monthly = {
        "year": year,
        "month": month,
        "total": 0,
        "success": 0,
        "failed": 0,
        "by_account": {},
        "daily_counts": {},
    }

    # 月内の全日次ファイルを集計
    for log_file in sorted(ANALYTICS_DIR.glob(f"{year}-{month:02d}-*.jsonl")):
        date_str = log_file.stem
        daily = get_daily_summary(date_str)
        monthly["total"] += daily["total"]
        monthly["success"] += daily["success"]
        monthly["failed"] += daily["failed"]
        monthly["daily_counts"][date_str] = daily["total"]

        for acc, counts in daily["by_account"].items():
            if acc not in monthly["by_account"]:
                monthly["by_account"][acc] = {"success": 0, "failed": 0}
            monthly["by_account"][acc]["success"] += counts["success"]
            monthly["by_account"][acc]["failed"] += counts["failed"]

    return monthly


def print_summary_report():
    """サマリーレポートをログに出力する"""
    logger.info("=== 投稿分析レポート ===")

    # 今日のサマリー
    daily = get_daily_summary()
    logger.info("--- 本日 (%s) ---", daily["date"])
    logger.info("  合計: %d件 (成功: %d, 失敗: %d)", daily["total"], daily["success"], daily["failed"])
    for acc, counts in daily["by_account"].items():
        logger.info("  [%s] 成功: %d, 失敗: %d", acc, counts["success"], counts["failed"])

    # 今月のサマリー
    monthly = get_monthly_summary()
    logger.info("--- 今月 (%d年%d月) ---", monthly["year"], monthly["month"])
    logger.info("  合計: %d件 (成功: %d, 失敗: %d)", monthly["total"], monthly["success"], monthly["failed"])
    if monthly["total"] > 0:
        success_rate = monthly["success"] / monthly["total"] * 100
        logger.info("  成功率: %.1f%%", success_rate)
