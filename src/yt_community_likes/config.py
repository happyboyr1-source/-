from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SlackConfig:
    webhook_url: str


@dataclass(frozen=True)
class NotifyConfig:
    method: str
    slack: SlackConfig | None = None


@dataclass(frozen=True)
class AppConfig:
    posts: list[str]
    notify: NotifyConfig


def load_config(path: Path) -> AppConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config must be a mapping.")

    posts = data.get("posts")
    if not isinstance(posts, list) or not all(isinstance(item, str) for item in posts):
        raise ValueError("posts must be a list of URLs.")

    notify_data = data.get("notify", {})
    if not isinstance(notify_data, dict):
        raise ValueError("notify must be a mapping.")

    method = str(notify_data.get("method", "stdout"))
    slack_config = None
    if method == "slack":
        slack_data = notify_data.get("slack")
        if not isinstance(slack_data, dict):
            raise ValueError("notify.slack must be a mapping when method is slack.")
        webhook_url = slack_data.get("webhook_url")
        if not isinstance(webhook_url, str) or not webhook_url:
            raise ValueError("notify.slack.webhook_url is required for slack notifications.")
        slack_config = SlackConfig(webhook_url=webhook_url)

    return AppConfig(posts=posts, notify=NotifyConfig(method=method, slack=slack_config))


def load_env_overrides(config: AppConfig) -> AppConfig:
    return config
