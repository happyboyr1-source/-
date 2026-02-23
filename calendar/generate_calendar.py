"""1ヶ月分の投稿カレンダーを自動生成するスクリプト

使い方:
    python calendar/generate_calendar.py
    python calendar/generate_calendar.py --account career --month 3 --year 2026
"""

import argparse
import json
import sys
import calendar as cal
from datetime import datetime, timezone, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import load_account_config, get_all_account_ids
from src.content_generator import generate_post, generate_thread, DAY_CONTENT_MAP
from src.compliance import clear_duplicate_cache

import random


JST = timezone(timedelta(hours=9))
OUTPUT_DIR = Path(__file__).parent


def generate_monthly_calendar(account_id, year, month):
    """1アカウント分の1ヶ月投稿カレンダーを生成する

    Args:
        account_id: "career", "english", "subscrip"
        year: 年
        month: 月

    Returns:
        dict: カレンダーデータ
    """
    config = load_account_config(account_id)
    genre = config["account"]["genre"]
    topics = config.get("topics", [])
    posting_times = config.get("posting_times_jst", [])
    days_in_month = cal.monthrange(year, month)[1]

    # 重複検出キャッシュをクリア
    clear_duplicate_cache()

    calendar_data = {
        "account_id": account_id,
        "account_name": config["account"]["display_name"],
        "year": year,
        "month": month,
        "generated_at": datetime.now(JST).isoformat(),
        "total_posts": 0,
        "days": [],
    }

    total_posts = 0
    topic_index = 0

    for day in range(1, days_in_month + 1):
        date_obj = datetime(year, month, day)
        weekday = date_obj.weekday()
        date_str = f"{year}-{month:02d}-{day:02d}"
        weekday_names = ["月", "火", "水", "木", "金", "土", "日"]

        content_schedule = DAY_CONTENT_MAP.get(weekday, DAY_CONTENT_MAP[0])
        day_data = {
            "date": date_str,
            "weekday": weekday_names[weekday],
            "posts": [],
        }

        for slot_index, content_type in enumerate(content_schedule):
            # 投稿時間
            time_str = posting_times[slot_index] if slot_index < len(posting_times) else "12:00"
            # ジッター追加
            parts = time_str.split(":")
            h, m = int(parts[0]), int(parts[1])
            jitter = random.randint(-3, 3)
            m = max(0, min(59, m + jitter))

            # トピックをローテーション
            topic = topics[topic_index % len(topics)] if topics else None
            topic_index += 1

            # スレッドの場合
            if content_type == "thread":
                thread_posts = generate_thread(genre, topic=topic, account_config=config)
                if thread_posts:
                    for tp in thread_posts:
                        post_entry = {
                            "id": f"{account_id}_{date_str}_{h:02d}{m:02d}_{slot_index}_thread",
                            "time": f"{h:02d}:{m:02d}",
                            "content_type": "thread",
                            "topic": topic or "general",
                            "text": tp["text"].strip(),
                            "part": tp.get("part", ""),
                            "char_count": len(tp["text"].strip()),
                            "status": "queued",
                        }
                        day_data["posts"].append(post_entry)
                        total_posts += 1
                else:
                    # スレッドテンプレートがなければtipsにフォールバック
                    post = generate_post(genre, "tips", topic=topic, account_config=config)
                    post_entry = {
                        "id": f"{account_id}_{date_str}_{h:02d}{m:02d}_{slot_index}",
                        "time": f"{h:02d}:{m:02d}",
                        "content_type": "tips",
                        "topic": topic or "general",
                        "text": post["text"].strip(),
                        "char_count": len(post["text"].strip()),
                        "has_pr": False,
                        "status": "queued",
                    }
                    day_data["posts"].append(post_entry)
                    total_posts += 1
            else:
                post = generate_post(genre, content_type, topic=topic, account_config=config)
                has_pr = content_type == "affiliate"

                post_entry = {
                    "id": f"{account_id}_{date_str}_{h:02d}{m:02d}_{slot_index}",
                    "time": f"{h:02d}:{m:02d}",
                    "content_type": content_type,
                    "topic": topic or "general",
                    "text": post["text"].strip(),
                    "char_count": len(post["text"].strip()),
                    "has_pr": has_pr,
                    "validation": {
                        "is_valid": post["validation"]["is_valid"],
                        "errors": post["validation"].get("errors", []),
                        "warnings": post["validation"].get("warnings", []),
                    },
                    "status": "queued",
                }
                day_data["posts"].append(post_entry)
                total_posts += 1

        calendar_data["days"].append(day_data)

    calendar_data["total_posts"] = total_posts
    return calendar_data


def save_calendar(calendar_data, output_dir=None):
    """カレンダーデータをJSONファイルに保存する"""
    if output_dir is None:
        output_dir = OUTPUT_DIR

    account_id = calendar_data["account_id"]
    month = calendar_data["month"]
    filename = f"{account_id}_month{month}.json"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(calendar_data, f, ensure_ascii=False, indent=2)

    print(f"  [SAVED] {filepath}")
    return filepath


def print_calendar_summary(calendar_data):
    """カレンダーの概要を表示する"""
    print(f"\n  アカウント: {calendar_data['account_name']}")
    print(f"  期間: {calendar_data['year']}年{calendar_data['month']}月")
    print(f"  総投稿数: {calendar_data['total_posts']}")

    # コンテンツタイプ別集計
    type_counts = {}
    error_count = 0
    for day in calendar_data["days"]:
        for post in day["posts"]:
            ct = post["content_type"]
            type_counts[ct] = type_counts.get(ct, 0) + 1
            if "validation" in post and not post["validation"]["is_valid"]:
                error_count += 1

    print("\n  コンテンツタイプ別:")
    for ct, count in sorted(type_counts.items()):
        print(f"    {ct}: {count}件")

    if error_count > 0:
        print(f"\n  警告: {error_count}件のバリデーションエラーがあります")

    # サンプル投稿表示（初日の最初の投稿）
    if calendar_data["days"]:
        first_day = calendar_data["days"][0]
        if first_day["posts"]:
            sample = first_day["posts"][0]
            print(f"\n  --- サンプル投稿 ({first_day['date']} {sample['time']}) ---")
            print(f"  {sample['text'][:150]}...")
            print(f"  文字数: {sample['char_count']}")


def main():
    parser = argparse.ArgumentParser(
        description="1ヶ月分の投稿カレンダーを生成"
    )
    parser.add_argument("--account", default="all",
                        choices=["career", "english", "subscrip", "all"],
                        help="対象アカウント（default: all）")
    parser.add_argument("--year", type=int, default=None,
                        help="年（default: 現在の年）")
    parser.add_argument("--month", type=int, default=None,
                        help="月（default: 翌月）")

    args = parser.parse_args()

    now = datetime.now(JST)
    year = args.year or now.year
    month = args.month or (now.month % 12 + 1)
    if month == 1 and args.month is None:
        year += 1

    account_ids = get_all_account_ids() if args.account == "all" else [args.account]

    print(f"=== 投稿カレンダー生成: {year}年{month}月 ===\n")

    for account_id in account_ids:
        print(f"--- {account_id} ---")
        calendar_data = generate_monthly_calendar(account_id, year, month)
        filepath = save_calendar(calendar_data)
        print_calendar_summary(calendar_data)
        print()

    print("=== 生成完了 ===")


if __name__ == "__main__":
    main()
