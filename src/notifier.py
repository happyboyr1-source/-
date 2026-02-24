"""エラー通知モジュール

投稿失敗やシステムエラー時にDiscord/LINE Webhookで通知する。
環境変数で通知先を設定可能。
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

from src.logger import get_logger


logger = get_logger(__name__)

JST = timezone(timedelta(hours=9))


def _get_webhook_url():
    """通知用Webhook URLを環境変数から取得する"""
    # Discord Webhook（優先）
    url = os.getenv("DISCORD_WEBHOOK_URL", "")
    if url:
        return "discord", url

    # LINE Notify
    url = os.getenv("LINE_NOTIFY_TOKEN", "")
    if url:
        return "line", url

    # Slack Webhook
    url = os.getenv("SLACK_WEBHOOK_URL", "")
    if url:
        return "slack", url

    return None, None


def _send_discord(webhook_url, title, message, level="error"):
    """Discord Webhookに通知を送信する"""
    colors = {"error": 0xFF0000, "warning": 0xFFA500, "info": 0x00FF00}
    color = colors.get(level, 0xFF0000)

    payload = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": color,
            "timestamp": datetime.now(JST).isoformat(),
            "footer": {"text": "X Affiliate Bot"},
        }]
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=10)


def _send_line(token, title, message, level="error"):
    """LINE Notifyに通知を送信する"""
    level_prefix = {"error": "[ERROR]", "warning": "[WARN]", "info": "[INFO]"}
    prefix = level_prefix.get(level, "[ERROR]")
    text = f"{prefix} {title}\n{message}"

    data = urllib.parse.urlencode({"message": text}).encode("utf-8")
    req = urllib.request.Request(
        "https://notify-api.line.me/api/notify",
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    urllib.request.urlopen(req, timeout=10)


def _send_slack(webhook_url, title, message, level="error"):
    """Slack Webhookに通知を送信する"""
    level_emoji = {"error": ":red_circle:", "warning": ":warning:", "info": ":white_check_mark:"}
    emoji = level_emoji.get(level, ":red_circle:")

    payload = {
        "text": f"{emoji} *{title}*\n{message}",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=10)


def send_notification(title, message, level="error"):
    """通知を送信する

    Args:
        title: 通知タイトル
        message: 通知メッセージ
        level: "error", "warning", "info"
    """
    service, url_or_token = _get_webhook_url()

    if service is None:
        logger.debug("通知先が設定されていません（DISCORD_WEBHOOK_URL / LINE_NOTIFY_TOKEN / SLACK_WEBHOOK_URL）")
        return

    try:
        if service == "discord":
            _send_discord(url_or_token, title, message, level)
        elif service == "line":
            _send_line(url_or_token, title, message, level)
        elif service == "slack":
            _send_slack(url_or_token, title, message, level)
        logger.debug("通知送信完了: [%s] %s", service, title)
    except (urllib.error.URLError, OSError) as e:
        logger.warning("通知送信失敗 (%s): %s", service, e)


def notify_post_failure(account_name, error_message):
    """投稿失敗を通知する"""
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    send_notification(
        title=f"投稿失敗: {account_name}",
        message=f"時刻: {now}\nアカウント: {account_name}\nエラー: {error_message}",
        level="error",
    )


def notify_rate_limit(remaining):
    """レート制限の警告を通知する"""
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    send_notification(
        title="レート制限警告",
        message=f"時刻: {now}\n月間残り投稿数: {remaining}/500",
        level="warning",
    )


def notify_system_start(mode="LIVE"):
    """システム起動を通知する"""
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    send_notification(
        title="Bot起動",
        message=f"時刻: {now}\nモード: {mode}",
        level="info",
    )


def notify_daily_summary(posted_count, failed_count, remaining):
    """日次サマリーを通知する"""
    now = datetime.now(JST).strftime("%Y-%m-%d JST")
    send_notification(
        title=f"日次レポート ({now})",
        message=(
            f"投稿成功: {posted_count}件\n"
            f"投稿失敗: {failed_count}件\n"
            f"月間残り: {remaining}/500"
        ),
        level="info" if failed_count == 0 else "warning",
    )
