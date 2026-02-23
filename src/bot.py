"""メインBotエントリポイント

全コンポーネントを統合し、CLIインターフェースを提供する。
"""

import argparse
import sys
from datetime import datetime, timezone, timedelta

from src.config_loader import (
    load_account_config,
    get_all_account_ids,
    validate_all_configs,
)
from src.content_generator import generate_post, generate_daily_posts
from src.poster import post_tweet, check_rate_limit
from src.scheduler import create_scheduler, run_due_posts
from src.compliance import clear_duplicate_cache


JST = timezone(timedelta(hours=9))


def cmd_validate(args):
    """設定ファイルのバリデーション"""
    print("=== 設定ファイル バリデーション ===\n")
    results = validate_all_configs()

    all_ok = True
    for account_id, errors in results.items():
        if errors:
            print(f"  [NG] {account_id}:")
            for err in errors:
                print(f"       - {err}")
            all_ok = False
        else:
            print(f"  [OK] {account_id}")

    print()
    if all_ok:
        print("全アカウントの設定が正常です")
    else:
        print("エラーのある設定を修正してください")
        sys.exit(1)


def cmd_generate(args):
    """投稿プレビュー生成"""
    account_id = args.account
    print(f"=== 投稿プレビュー: {account_id} ===\n")

    config = load_account_config(account_id)
    genre = config["account"]["genre"]
    topics = config.get("topics", [])
    now = datetime.now(JST)
    weekday = now.weekday()

    posts = generate_daily_posts(genre, weekday, account_config=config, topics=topics)

    for i, post in enumerate(posts):
        print(f"--- 投稿 {i + 1} ({post['content_type']}) ---")
        print(post["text"])
        v = post["validation"]
        print(f"  文字数: {v['char_count']}/280")
        if v["errors"]:
            print(f"  エラー: {', '.join(v['errors'])}")
        if v["warnings"]:
            print(f"  警告: {', '.join(v['warnings'])}")
        print()


def cmd_post(args):
    """即時投稿"""
    dry_run = args.dry_run
    account_ids = get_all_account_ids() if args.account == "all" else [args.account]

    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"=== 即時投稿 ({mode}) ===\n")

    # レート制限チェック
    can_post, remaining, limit_error = check_rate_limit()
    print(f"  残り投稿可能数: {remaining}/500")
    if not can_post:
        print(f"  [BLOCKED] {limit_error}")
        return

    for account_id in account_ids:
        print(f"\n--- {account_id} ---")
        config = load_account_config(account_id)
        genre = config["account"]["genre"]
        topics = config.get("topics", [])

        import random
        topic = random.choice(topics) if topics else None
        post = generate_post(genre, "tips", topic=topic, account_config=config)

        if post["validation"]["is_valid"]:
            result = post_tweet(config, post["text"], dry_run=dry_run)
            if result["success"]:
                print(f"  投稿成功: {post['text'][:50]}...")
            else:
                print(f"  投稿失敗: {result['error']}")
        else:
            errors = ", ".join(post["validation"]["errors"])
            print(f"  バリデーションエラー: {errors}")


def cmd_schedule(args):
    """スケジューラー起動"""
    dry_run = args.dry_run
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"=== スケジューラー起動 ({mode}) ===\n")

    if args.due:
        # cron用：現在時刻で実行すべき投稿を処理
        print("  cron モード: 実行予定の投稿を確認中...\n")
        run_due_posts(dry_run=dry_run)
    else:
        # 常駐モード
        print("  常駐モード: Ctrl+C で停止\n")
        scheduler = create_scheduler(dry_run=dry_run)
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("\n  スケジューラーを停止しました")


def cmd_status(args):
    """ステータス表示"""
    print("=== システムステータス ===\n")

    # レート制限
    can_post, remaining, limit_error = check_rate_limit()
    print(f"  月間投稿残: {remaining}/500")
    if not can_post:
        print(f"  警告: {limit_error}")

    # 各アカウント状態
    print("\n--- アカウント ---")
    for account_id in get_all_account_ids():
        try:
            config = load_account_config(account_id)
            name = config["account"]["display_name"]
            posts_per_day = config["content_strategy"]["posts_per_day"]
            times = config.get("posting_times_jst", [])
            print(f"  [{account_id}] {name}")
            print(f"    投稿/日: {posts_per_day}")
            print(f"    投稿時間: {', '.join(times)}")
        except Exception as e:
            print(f"  [{account_id}] エラー: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="X (Twitter) アフィリエイト自動化Bot"
    )
    subparsers = parser.add_subparsers(dest="command", help="コマンド")

    # validate
    sub = subparsers.add_parser("validate", help="設定ファイルのバリデーション")
    sub.set_defaults(func=cmd_validate)

    # generate
    sub = subparsers.add_parser("generate", help="投稿プレビュー生成")
    sub.add_argument("--account", required=True,
                     choices=["career", "english", "subscrip"],
                     help="対象アカウント")
    sub.set_defaults(func=cmd_generate)

    # post
    sub = subparsers.add_parser("post", help="即時投稿")
    sub.add_argument("--account", default="all",
                     help="対象アカウント（all=全アカウント）")
    sub.add_argument("--dry-run", action="store_true",
                     help="ドライラン（API呼び出しなし）")
    sub.set_defaults(func=cmd_post)

    # schedule
    sub = subparsers.add_parser("schedule", help="スケジューラー起動")
    sub.add_argument("--dry-run", action="store_true",
                     help="ドライラン")
    sub.add_argument("--due", action="store_true",
                     help="cron用: 現在実行すべき投稿のみ処理")
    sub.set_defaults(func=cmd_schedule)

    # status
    sub = subparsers.add_parser("status", help="ステータス表示")
    sub.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
