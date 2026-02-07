from __future__ import annotations

import argparse
import time
from pathlib import Path

import schedule
from dotenv import load_dotenv

from yt_community_likes.config import load_config
from yt_community_likes.fetcher import LikeFetchError, fetch_like_counts
from yt_community_likes.notifier import Notification, build_notifier


def _summarize_results(results: list[tuple[str, int]]) -> str:
    lines = []
    for index, (url, count) in enumerate(results, start=1):
        lines.append(f"{index}. {count:,} いいね - {url}")
    return "\n".join(lines)


def _run_once(config_path: Path) -> None:
    config = load_config(config_path)
    notifier = build_notifier(config.notify)

    try:
        likes = fetch_like_counts(config.posts)
    except LikeFetchError as exc:
        notifier.send(
            Notification(
                title="YouTubeコミュニティ投稿の取得に失敗しました",
                body=str(exc),
            )
        )
        return

    ranked = sorted(((item.url, item.like_count) for item in likes), key=lambda x: x[1], reverse=True)
    summary = _summarize_results(ranked)
    notifier.send(Notification(title="YouTubeコミュニティ投稿のいいねランキング", body=summary))


def _schedule_daily(config_path: Path, at_time: str) -> None:
    schedule.every().day.at(at_time).do(_run_once, config_path=config_path)
    while True:
        schedule.run_pending()
        time.sleep(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare YouTube community post likes.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config file.",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("run", help="Run once.")

    schedule_parser = subparsers.add_parser("schedule", help="Run daily on schedule.")
    schedule_parser.add_argument(
        "--time",
        default="09:00",
        help="Time in 24h format (HH:MM).",
    )

    return parser


def main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "schedule":
        _schedule_daily(args.config, args.time)
        return

    _run_once(args.config)


if __name__ == "__main__":
    main()
