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
from src.logger import setup_logging, get_logger
from src.analytics import print_summary_report


logger = get_logger(__name__)

JST = timezone(timedelta(hours=9))


def cmd_validate(args):
    """設定ファイルのバリデーション"""
    logger.info("=== 設定ファイル バリデーション ===")
    results = validate_all_configs()

    all_ok = True
    for account_id, errors in results.items():
        if errors:
            logger.error("[NG] %s: %s", account_id, "; ".join(errors))
            all_ok = False
        else:
            logger.info("[OK] %s", account_id)

    if all_ok:
        logger.info("全アカウントの設定が正常です")
    else:
        logger.error("エラーのある設定を修正してください")
        sys.exit(1)


def cmd_generate(args):
    """投稿プレビュー生成"""
    account_id = args.account
    logger.info("=== 投稿プレビュー: %s ===", account_id)

    config = load_account_config(account_id)
    genre = config["account"]["genre"]
    topics = config.get("topics", [])
    now = datetime.now(JST)
    weekday = now.weekday()

    posts = generate_daily_posts(genre, weekday, account_config=config, topics=topics)

    for i, post in enumerate(posts):
        logger.info("--- 投稿 %d (%s) ---", i + 1, post["content_type"])
        logger.info("%s", post["text"])
        v = post["validation"]
        logger.info("  文字数: %d/280", v["char_count"])
        if v["errors"]:
            logger.error("  エラー: %s", ", ".join(v["errors"]))
        if v["warnings"]:
            logger.warning("  警告: %s", ", ".join(v["warnings"]))


def cmd_post(args):
    """即時投稿"""
    dry_run = args.dry_run
    account_ids = get_all_account_ids() if args.account == "all" else [args.account]

    mode = "DRY RUN" if dry_run else "LIVE"
    logger.info("=== 即時投稿 (%s) ===", mode)

    # レート制限チェック
    can_post, remaining, limit_error = check_rate_limit()
    logger.info("残り投稿可能数: %d/500", remaining)
    if not can_post:
        logger.warning("[BLOCKED] %s", limit_error)
        return

    for account_id in account_ids:
        logger.info("--- %s ---", account_id)
        config = load_account_config(account_id)
        genre = config["account"]["genre"]
        topics = config.get("topics", [])

        import random
        topic = random.choice(topics) if topics else None
        post = generate_post(genre, "tips", topic=topic, account_config=config)

        if post["validation"]["is_valid"]:
            result = post_tweet(config, post["text"], dry_run=dry_run)
            if result["success"]:
                logger.info("[%s] 投稿成功: %s...", account_id, post["text"][:50])
            else:
                logger.error("[%s] 投稿失敗: %s", account_id, result["error"])
        else:
            errors = ", ".join(post["validation"]["errors"])
            logger.error("[%s] バリデーションエラー: %s", account_id, errors)


def cmd_schedule(args):
    """スケジューラー起動"""
    dry_run = args.dry_run
    mode = "DRY RUN" if dry_run else "LIVE"
    logger.info("=== スケジューラー起動 (%s) ===", mode)

    if args.due:
        logger.info("cron モード: 実行予定の投稿を確認中...")
        run_due_posts(dry_run=dry_run)
    else:
        logger.info("常駐モード: Ctrl+C で停止")
        scheduler = create_scheduler(dry_run=dry_run)
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("スケジューラーを停止しました")


def cmd_status(args):
    """ステータス表示"""
    logger.info("=== システムステータス ===")

    # レート制限
    can_post, remaining, limit_error = check_rate_limit()
    logger.info("月間投稿残: %d/500", remaining)
    if not can_post:
        logger.warning("警告: %s", limit_error)

    # 各アカウント状態
    logger.info("--- アカウント ---")
    for account_id in get_all_account_ids():
        try:
            config = load_account_config(account_id)
            name = config["account"]["display_name"]
            posts_per_day = config["content_strategy"]["posts_per_day"]
            times = config.get("posting_times_jst", [])
            logger.info("[%s] %s", account_id, name)
            logger.info("  投稿/日: %d", posts_per_day)
            logger.info("  投稿時間: %s", ", ".join(times))
        except Exception as e:
            logger.error("[%s] エラー: %s", account_id, e)


def cmd_report(args):
    """投稿分析レポートを表示する"""
    print_summary_report()


def cmd_health(args):
    """ヘルスチェック（Docker/監視システム用）

    以下をチェックし、異常があれば非ゼロで終了:
    - 設定ファイルの読み込み
    - レート制限の状態
    - テンプレートの存在
    - データディレクトリの書き込み可能性
    """
    from pathlib import Path

    checks = []

    # 1. 設定ファイルチェック
    try:
        results = validate_all_configs()
        config_errors = sum(1 for errs in results.values() if errs)
        if config_errors > 0:
            checks.append(("config", "FAIL", f"{config_errors}件のエラー"))
        else:
            checks.append(("config", "OK", f"{len(results)}アカウント正常"))
    except Exception as e:
        checks.append(("config", "FAIL", str(e)))

    # 2. レート制限チェック
    try:
        can_post, remaining, limit_error = check_rate_limit()
        if can_post:
            checks.append(("rate_limit", "OK", f"残り{remaining}/500"))
        else:
            checks.append(("rate_limit", "WARN", limit_error))
    except Exception as e:
        checks.append(("rate_limit", "FAIL", str(e)))

    # 3. テンプレートディレクトリチェック
    template_dir = Path(__file__).parent.parent / "templates"
    template_count = len(list(template_dir.glob("**/*.yaml")))
    if template_count > 0:
        checks.append(("templates", "OK", f"{template_count}テンプレート"))
    else:
        checks.append(("templates", "FAIL", "テンプレートが見つかりません"))

    # 4. データディレクトリの書き込みチェック
    data_dir = Path(__file__).parent.parent / "data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        test_file = data_dir / ".health_check"
        test_file.write_text("ok")
        test_file.unlink()
        checks.append(("data_dir", "OK", "書き込み可能"))
    except OSError as e:
        checks.append(("data_dir", "FAIL", str(e)))

    # 結果出力
    has_failure = False
    for name, status, detail in checks:
        logger.info("[%s] %s: %s", status, name, detail)
        if status == "FAIL":
            has_failure = True

    if has_failure:
        sys.exit(1)


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

    # report
    sub = subparsers.add_parser("report", help="投稿分析レポート")
    sub.set_defaults(func=cmd_report)

    # health
    sub = subparsers.add_parser("health", help="ヘルスチェック")
    sub.set_defaults(func=cmd_health)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    setup_logging()
    args.func(args)


if __name__ == "__main__":
    main()
