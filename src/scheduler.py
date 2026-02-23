"""投稿スケジューラー

APSchedulerを使用して、各アカウントの投稿を
指定された時間に自動実行する。
JST（日本標準時）ベースでスケジュール管理。
"""

import random
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config_loader import load_account_config, get_all_account_ids
from src.content_generator import generate_post, DAY_CONTENT_MAP
from src.compliance import validate_post
from src.poster import post_tweet


# JST タイムゾーン
JST = timezone(timedelta(hours=9))

# 投稿時間のジッター（分）- 完全な定時投稿を避ける
JITTER_MINUTES = 5


def get_posting_schedule(account_config):
    """アカウントの投稿スケジュールを取得する

    Returns:
        list[dict]: [{hour, minute, content_type}]
    """
    times = account_config.get("posting_times_jst", [])
    schedule = []

    for time_str in times:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        # ジッターを追加（±5分のランダムなずれ）
        jitter = random.randint(-JITTER_MINUTES, JITTER_MINUTES)
        adjusted_minute = max(0, min(59, minute + jitter))
        schedule.append({"hour": hour, "minute": adjusted_minute})

    return schedule


def _get_content_type_for_slot(weekday, slot_index):
    """曜日と時間スロットからコンテンツタイプを決定する"""
    schedule = DAY_CONTENT_MAP.get(weekday, DAY_CONTENT_MAP[0])
    if slot_index < len(schedule):
        return schedule[slot_index]
    return "tips"


def execute_scheduled_post(account_id, slot_index, dry_run=False):
    """スケジュールされた投稿を実行する

    Args:
        account_id: アカウントID
        slot_index: 時間スロットインデックス（0-4）
        dry_run: ドライラン
    """
    try:
        config = load_account_config(account_id)
        genre = config["account"]["genre"]
        now = datetime.now(JST)
        weekday = now.weekday()

        content_type = _get_content_type_for_slot(weekday, slot_index)

        # トピックリストからランダム選択
        topics = config.get("topics", [])
        topic = random.choice(topics) if topics else None

        # 投稿生成
        post = generate_post(genre, content_type, topic=topic, account_config=config)

        if not post["validation"]["is_valid"]:
            errors = ", ".join(post["validation"]["errors"])
            print(f"  [SKIP] [{account_id}] バリデーションエラー: {errors}")
            return

        # 投稿実行
        result = post_tweet(config, post["text"], dry_run=dry_run)

        if result["success"]:
            status = "DRY RUN" if dry_run else "SUCCESS"
            print(f"  [{status}] [{account_id}] slot={slot_index} type={content_type}")
        else:
            print(f"  [FAIL] [{account_id}] {result['error']}")

    except Exception as e:
        print(f"  [ERROR] [{account_id}] スケジュール投稿でエラー: {e}")


def create_scheduler(dry_run=False):
    """全アカウントのスケジューラーを作成する

    Args:
        dry_run: Trueならドライランモード

    Returns:
        BlockingScheduler: 設定済みスケジューラー
    """
    scheduler = BlockingScheduler(timezone="Asia/Tokyo")

    account_ids = get_all_account_ids()

    for account_id in account_ids:
        try:
            config = load_account_config(account_id)
            schedule = get_posting_schedule(config)

            for slot_index, slot in enumerate(schedule):
                job_id = f"{account_id}_slot_{slot_index}"
                trigger = CronTrigger(
                    hour=slot["hour"],
                    minute=slot["minute"],
                    timezone="Asia/Tokyo"
                )

                scheduler.add_job(
                    execute_scheduled_post,
                    trigger=trigger,
                    args=[account_id, slot_index, dry_run],
                    id=job_id,
                    name=f"{account_id} - Slot {slot_index} ({slot['hour']}:{slot['minute']:02d})",
                    replace_existing=True,
                )

                print(f"  [SCHEDULED] {account_id} slot {slot_index}: "
                      f"{slot['hour']}:{slot['minute']:02d} JST")

        except Exception as e:
            print(f"  [ERROR] {account_id} のスケジュール設定に失敗: {e}")

    return scheduler


def run_due_posts(dry_run=False):
    """現在時刻で投稿すべきものを即時実行する（cron用）

    15分間隔のcronから呼び出す想定。
    現在時刻から±10分以内のスロットを対象にする。
    """
    now = datetime.now(JST)
    current_minutes = now.hour * 60 + now.minute

    account_ids = get_all_account_ids()

    for account_id in account_ids:
        try:
            config = load_account_config(account_id)
            times = config.get("posting_times_jst", [])

            for slot_index, time_str in enumerate(times):
                parts = time_str.split(":")
                slot_minutes = int(parts[0]) * 60 + int(parts[1])

                # ±10分以内なら実行
                if abs(current_minutes - slot_minutes) <= 10:
                    print(f"  [DUE] {account_id} slot {slot_index} ({time_str})")
                    execute_scheduled_post(account_id, slot_index, dry_run=dry_run)

        except Exception as e:
            print(f"  [ERROR] {account_id}: {e}")
