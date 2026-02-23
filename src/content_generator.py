"""投稿コンテンツ生成エンジン

Jinja2テンプレートとランダム要素を組み合わせて、
各アカウントのペルソナに合った投稿文を自動生成する。
AI API不要で動作可能なテンプレートベースの生成システム。
"""

import random
from pathlib import Path

import yaml
from jinja2 import Template

from src.compliance import validate_post


TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# コンテンツタイプ定義
CONTENT_TYPES = ["tips", "engagement", "affiliate", "thread"]

# 曜日ごとのコンテンツタイプマッピング
DAY_CONTENT_MAP = {
    0: ["tips", "tips", "engagement", "tips", "tips"],           # 月: Tips中心
    1: ["tips", "tips", "engagement", "tips", "tips"],           # 火: トレンド
    2: ["tips", "tips", "engagement", "tips", "affiliate"],      # 水: ハウツー+PR
    3: ["engagement", "tips", "engagement", "tips", "tips"],     # 木: Q&A
    4: ["tips", "tips", "engagement", "affiliate", "affiliate"], # 金: おすすめ+PR
    5: ["thread", "tips", "engagement", "tips", "affiliate"],    # 土: スレッド+PR
    6: ["engagement", "tips", "engagement", "tips", "engagement"], # 日: エンゲージメント
}


def load_templates(genre):
    """指定ジャンルの全テンプレートを読み込む

    Args:
        genre: "career", "english", "subscrip"

    Returns:
        dict: {content_type: [template_dicts]}
    """
    templates = {}
    genre_dir = TEMPLATE_DIR / genre
    if not genre_dir.exists():
        raise FileNotFoundError(f"テンプレートディレクトリが見つかりません: {genre_dir}")

    for content_type in CONTENT_TYPES:
        template_file = genre_dir / f"{content_type}.yaml"
        if template_file.exists():
            with open(template_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                templates[content_type] = data.get("templates", [])
        else:
            templates[content_type] = []

    return templates


def _render_template(template_str, variables):
    """Jinja2テンプレートを変数で展開する"""
    tmpl = Template(template_str)
    return tmpl.render(**variables)


def generate_post(genre, content_type, topic=None, account_config=None):
    """1件の投稿テキストを生成する

    Args:
        genre: "career", "english", "subscrip"
        content_type: "tips", "engagement", "affiliate", "thread"
        topic: トピック（Noneの場合ランダム選択）
        account_config: アカウント設定（バリデーション用）

    Returns:
        dict: {
            "text": str,
            "content_type": str,
            "topic": str,
            "validation": dict
        }
    """
    templates = load_templates(genre)
    type_templates = templates.get(content_type, [])

    if not type_templates:
        return {
            "text": "",
            "content_type": content_type,
            "topic": topic,
            "validation": {"is_valid": False, "errors": ["テンプレートがありません"]},
        }

    # ランダムにテンプレートを選択
    template_entry = random.choice(type_templates)
    template_str = template_entry["template"]

    # 変数候補からランダムに選択
    variables = {}
    for var_name, var_options in template_entry.get("variables", {}).items():
        if isinstance(var_options, list):
            variables[var_name] = random.choice(var_options)
        else:
            variables[var_name] = var_options

    # トピックが指定されていれば上書き
    if topic:
        variables["topic"] = topic

    # テンプレート展開
    text = _render_template(template_str, variables)

    # バリデーション
    validation = {"is_valid": True, "char_count": len(text), "errors": [], "warnings": []}
    if account_config:
        # content_type を compliance 用のタイプに変換
        compliance_type = "direct_promo" if content_type == "affiliate" else content_type
        validation = validate_post(text, compliance_type, account_config)

    return {
        "text": text,
        "content_type": content_type,
        "topic": topic or template_entry.get("topic", "general"),
        "validation": validation,
    }


def generate_daily_posts(genre, weekday, account_config=None, topics=None):
    """1日分の投稿（5件）を生成する

    Args:
        genre: アカウントジャンル
        weekday: 曜日（0=月曜日, 6=日曜日）
        account_config: アカウント設定
        topics: トピックリスト

    Returns:
        list[dict]: 5件の投稿データ
    """
    content_schedule = DAY_CONTENT_MAP.get(weekday, DAY_CONTENT_MAP[0])
    posts = []

    for i, content_type in enumerate(content_schedule):
        topic = None
        if topics:
            topic = topics[i % len(topics)]

        post = generate_post(genre, content_type, topic=topic,
                             account_config=account_config)
        posts.append(post)

    return posts


def generate_thread(genre, topic=None, account_config=None):
    """スレッド投稿（3-5件の連続ツイート）を生成する

    Args:
        genre: アカウントジャンル
        topic: スレッドのトピック
        account_config: アカウント設定

    Returns:
        list[dict]: スレッドを構成する投稿データのリスト
    """
    templates = load_templates(genre)
    thread_templates = templates.get("thread", [])

    if not thread_templates:
        return []

    template_entry = random.choice(thread_templates)
    thread_parts = template_entry.get("parts", [])

    thread_posts = []
    total = len(thread_parts)

    for i, part in enumerate(thread_parts):
        variables = {}
        for var_name, var_options in part.get("variables", {}).items():
            if isinstance(var_options, list):
                variables[var_name] = random.choice(var_options)
            else:
                variables[var_name] = var_options

        variables["part_num"] = i + 1
        variables["total_parts"] = total

        text = _render_template(part["template"], variables)
        thread_posts.append({
            "text": text,
            "content_type": "thread",
            "part": f"{i + 1}/{total}",
            "topic": topic or template_entry.get("topic", "general"),
        })

    return thread_posts
