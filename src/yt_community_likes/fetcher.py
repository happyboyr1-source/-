from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

import requests


@dataclass(frozen=True)
class PostLike:
    url: str
    like_count: int


class LikeFetchError(RuntimeError):
    pass


_YT_INITIAL_DATA_RE = re.compile(r"ytInitialData\s*=\s*(\{.*?\});", re.DOTALL)
_DIGITS_RE = re.compile(r"\d+")


def fetch_like_count(url: str, timeout_s: int = 20) -> PostLike:
    response = requests.get(
        url,
        timeout=timeout_s,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        },
    )
    response.raise_for_status()

    match = _YT_INITIAL_DATA_RE.search(response.text)
    if not match:
        raise LikeFetchError("Could not locate ytInitialData on the page.")

    raw_json = match.group(1)
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise LikeFetchError("Failed to decode ytInitialData JSON.") from exc

    like_count = _extract_like_count(payload)
    if like_count is None:
        raise LikeFetchError("Could not find like count in ytInitialData.")

    return PostLike(url=url, like_count=like_count)


def fetch_like_counts(urls: Iterable[str]) -> list[PostLike]:
    results = []
    for url in urls:
        results.append(fetch_like_count(url))
    return results


def _extract_like_count(payload: Any) -> int | None:
    counts: list[int] = []
    for value in _walk(payload):
        if not isinstance(value, dict):
            continue
        if "voteCount" in value:
            count = _parse_count_text(value["voteCount"])
            if count is not None:
                counts.append(count)
        if "likeCount" in value:
            count = _parse_count_text(value["likeCount"])
            if count is not None:
                counts.append(count)
        if "label" in value and isinstance(value["label"], str):
            label = value["label"]
            if "like" in label.lower() or "いいね" in label:
                count = _parse_count_text(label)
                if count is not None:
                    counts.append(count)

    if not counts:
        return None

    return max(counts)


def _parse_count_text(value: Any) -> int | None:
    if isinstance(value, dict):
        value = value.get("simpleText") or value.get("runs") or value.get("label")
    if isinstance(value, list):
        value = "".join(part.get("text", "") for part in value if isinstance(part, dict))
    if not isinstance(value, str):
        return None

    digits = "".join(_DIGITS_RE.findall(value))
    if not digits:
        return None
    return int(digits)


def _walk(node: Any) -> Iterable[Any]:
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        if isinstance(current, dict):
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
