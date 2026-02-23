"""投稿を一括生成するスクリプト

使い方:
    python scripts/generate_posts.py
    python scripts/generate_posts.py --account career --count 10
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import load_account_config, get_all_account_ids
from src.content_generator import generate_post, CONTENT_TYPES
from src.compliance import clear_duplicate_cache

import random


def main():
    parser = argparse.ArgumentParser(description="投稿を一括生成")
    parser.add_argument("--account", default="all",
                        choices=["career", "english", "subscrip", "all"],
                        help="対象アカウント")
    parser.add_argument("--count", type=int, default=5,
                        help="生成する投稿数（default: 5）")
    parser.add_argument("--type", default=None,
                        choices=["tips", "engagement", "affiliate", "thread"],
                        help="コンテンツタイプ（指定なしでランダム）")
    args = parser.parse_args()

    account_ids = get_all_account_ids() if args.account == "all" else [args.account]

    print(f"=== 投稿一括生成（{args.count}件/アカウント） ===\n")

    for account_id in account_ids:
        print(f"--- {account_id} ---\n")
        clear_duplicate_cache()

        config = load_account_config(account_id)
        genre = config["account"]["genre"]
        topics = config.get("topics", [])

        valid_count = 0
        error_count = 0

        for i in range(args.count):
            content_type = args.type or random.choice(["tips", "engagement", "tips", "engagement", "affiliate"])
            topic = random.choice(topics) if topics else None

            post = generate_post(genre, content_type, topic=topic, account_config=config)

            status = "OK" if post["validation"]["is_valid"] else "NG"
            if post["validation"]["is_valid"]:
                valid_count += 1
            else:
                error_count += 1

            print(f"  [{status}] #{i+1} ({content_type}) [{post['validation']['char_count']}字]")
            print(f"  {post['text'][:80]}...")
            if post["validation"]["errors"]:
                print(f"  エラー: {', '.join(post['validation']['errors'])}")
            print()

        print(f"  結果: {valid_count}件成功 / {error_count}件エラー\n")


if __name__ == "__main__":
    main()
