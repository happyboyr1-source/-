"""ロギング設定モジュール

本番運用向けのロギング設定を提供する。
- コンソール出力（カラー付き）
- ローテーション付きファイル出力
- アカウント別ログ識別
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ファイルログのデフォルト設定
MAX_LOG_BYTES = 5 * 1024 * 1024  # 5MB
BACKUP_COUNT = 5


def setup_logging(log_level=None):
    """アプリケーション全体のロギングを設定する

    Args:
        log_level: ログレベル文字列 ("DEBUG", "INFO", "WARNING", "ERROR")
                   Noneの場合は環境変数 LOG_LEVEL またはデフォルト INFO
    """
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    level = getattr(logging, log_level, logging.INFO)

    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 既存ハンドラーをクリア（重複防止）
    root_logger.handlers.clear()

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ファイルハンドラー（ログディレクトリが作成可能な場合のみ）
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # メインログファイル
        file_handler = RotatingFileHandler(
            LOG_DIR / "bot.log",
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        )
        root_logger.addHandler(file_handler)

        # エラー専用ログファイル
        error_handler = RotatingFileHandler(
            LOG_DIR / "error.log",
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        )
        root_logger.addHandler(error_handler)

    except OSError:
        # ログディレクトリが作成できない場合はコンソールのみ
        pass

    # 外部ライブラリのログレベルを抑制
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("tweepy").setLevel(logging.WARNING)


def get_logger(name):
    """モジュール用ロガーを取得する

    Args:
        name: モジュール名（通常は __name__）

    Returns:
        logging.Logger
    """
    return logging.getLogger(name)
