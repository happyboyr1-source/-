"""全アカウントのBotを起動する

使い方:
    python scripts/run_all.py
    python scripts/run_all.py --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import validate_all_configs
from src.scheduler import create_scheduler


def main():
    parser = argparse.ArgumentParser(description="全アカウントBotを起動")
    parser.add_argument("--dry-run", action="store_true",
                        help="ドライラン（API呼び出しなし）")
    args = parser.parse_args()

    print("=== X アフィリエイトBot 起動 ===\n")

    # 設定バリデーション
    print("設定ファイルを検証中...")
    results = validate_all_configs()
    has_error = False
    for account_id, errors in results.items():
        if errors:
            print(f"  [NG] {account_id}: {', '.join(errors)}")
            has_error = True
        else:
            print(f"  [OK] {account_id}")

    if has_error:
        print("\n設定エラーがあります。修正してから再実行してください。")
        sys.exit(1)

    print("\n設定OK。スケジューラーを起動します。\n")

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"モード: {mode}")
    print("Ctrl+C で停止\n")

    scheduler = create_scheduler(dry_run=args.dry_run)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nBotを停止しました。")


if __name__ == "__main__":
    main()
