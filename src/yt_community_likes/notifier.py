from __future__ import annotations

from dataclasses import dataclass

import requests

from yt_community_likes.config import NotifyConfig, SlackConfig


@dataclass(frozen=True)
class Notification:
    title: str
    body: str


class Notifier:
    def send(self, notification: Notification) -> None:
        raise NotImplementedError


class StdoutNotifier(Notifier):
    def send(self, notification: Notification) -> None:
        print(f"{notification.title}\n{notification.body}")


class SlackNotifier(Notifier):
    def __init__(self, config: SlackConfig) -> None:
        self._config = config

    def send(self, notification: Notification) -> None:
        response = requests.post(
            self._config.webhook_url,
            json={"text": f"*{notification.title}*\n{notification.body}"},
            timeout=10,
        )
        response.raise_for_status()


def build_notifier(config: NotifyConfig) -> Notifier:
    if config.method == "slack":
        if not config.slack:
            raise ValueError("Slack config is required when method is slack.")
        return SlackNotifier(config.slack)
    if config.method == "stdout":
        return StdoutNotifier()
    raise ValueError(f"Unknown notify method: {config.method}")
