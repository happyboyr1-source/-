"""テスト投稿スクリプト

1件のテスト投稿を実行する。デフォルトはドライランモード。

使い方:
    python scripts/test_post.py --account career          # ドライラン
    python scripts/test_post.py --account career --live    # 実際に投稿
    python scripts/test_post.py --dry-run                  # 全アカウントドライラン
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import load_account_config, get_all_account_ids
from src.content_generator import generate_post
from src.poster import post_tweet, check_rate_limit

import random


def main():
    parser = argparse.ArgumentParser(description="テスト投稿")
    parser.add_argument("--account", default=None,
                        choices=["career", "english", "subscrip"],
                        help="対象アカウント")
    parser.add_argument("--live", action="store_true",
                        help="実際にAPIを使って投稿する（デフォルトはドライラン）")
    parser.add_argument("--dry-run", action="store_true",
                        help="全アカウントでドライラン")
    parser.add_argument("--type", default="tips",
                        choices=["tips", "engagement", "affiliate"],
                        help="投稿タイプ（default: tips）")
    args = parser.parse_args()

    dry_run = not args.live

    if args.dry_run:
        account_ids = get_all_account_ids()
        dry_run = True
    elif args.account:
        account_ids = [args.account]
    else:
        print("--account または --dry-run を指定してください")
        sys.exit(1)

    mode = "DRY RUN" if dry_run else "LIVE (実際に投稿します！)"
    print(f"=== テスト投稿 ({mode}) ===\n")

    # レート制限チェック
    can_post, remaining, limit_error = check_rate_limit()
    print(f"  月間残り投稿数: {remaining}/500")
    if not can_post and not dry_run:
        print(f"  [BLOCKED] {limit_error}")
        sys.exit(1)

    for account_id in account_ids:
        print(f"\n--- {account_id} ---")
        config = load_account_config(account_id)
        genre = config["account"]["genre"]
        topics = config.get("topics", [])
        topic = random.choice(topics) if topics else None

        # 投稿生成
        post = generate_post(genre, args.type, topic=topic, account_config=config)

        print(f"  タイプ: {post['content_type']}")
        print(f"  トピック: {post['topic']}")
        print(f"  文字数: {post['validation']['char_count']}/280")
        print(f"  テキスト:")
        print(f"  ----")
        for line in post["text"].strip().split("\n"):
            print(f"  {line}")
        print(f"  ----")

        if post["validation"]["errors"]:
            print(f"  エラー: {', '.join(post['validation']['errors'])}")
            continue

        if post["validation"]["warnings"]:
            print(f"  警告: {', '.join(post['validation']['warnings'])}")

        # 投稿実行
        result = post_tweet(config, post["text"], dry_run=dry_run)
        if result["success"]:
            print(f"  結果: 成功 (ID: {result['tweet_id']})")
        else:
            print(f"  結果: 失敗 ({result['error']})")

    print(f"\n=== テスト完了 ===")


if __name__ == "__main__":
    main()
