"""全アカウントのBotを起動する

使い方:
    python scripts/run_all.py
    python scripts/run_all.py --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logger import setup_logging, get_logger
from src.config_loader import validate_all_configs
from src.scheduler import create_scheduler
from src.notifier import notify_system_start

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="全アカウントBotを起動")
    parser.add_argument("--dry-run", action="store_true",
                        help="ドライラン（API呼び出しなし）")
    args = parser.parse_args()

    setup_logging()

    logger.info("=== X アフィリエイトBot 起動 ===")

    # 設定バリデーション
    logger.info("設定ファイルを検証中...")
    results = validate_all_configs()
    has_error = False
    for account_id, errors in results.items():
        if errors:
            logger.error("[NG] %s: %s", account_id, ", ".join(errors))
            has_error = True
        else:
            logger.info("[OK] %s", account_id)

    if has_error:
        logger.error("設定エラーがあります。修正してから再実行してください。")
        sys.exit(1)

    logger.info("設定OK。スケジューラーを起動します。")

    mode = "DRY RUN" if args.dry_run else "LIVE"
    logger.info("モード: %s", mode)
    logger.info("Ctrl+C で停止")

    notify_system_start(mode)

    scheduler = create_scheduler(dry_run=args.dry_run)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Botを停止しました。")


if __name__ == "__main__":
    main()
