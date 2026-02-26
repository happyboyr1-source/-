"""ステマ規制準拠チェック・投稿バリデーション

日本のステマ規制（2023年10月施行）に準拠するため、
アフィリエイト投稿には必ず #PR を明記する。
"""

import hashlib


# X(Twitter)のツイート文字数上限
MAX_TWEET_CHARS = 280

# URLはXの仕様で23文字としてカウントされる
URL_CHAR_COUNT = 23

# 過去の投稿ハッシュを保持（重複検出用）
_posted_hashes = set()


def check_pr_label(text, content_type, compliance_config):
    """PR表記の存在をチェックする

    Args:
        text: 投稿テキスト
        content_type: "direct_promo", "soft_sell" 等
        compliance_config: アカウントのcompliance設定

    Returns:
        tuple: (is_valid, error_message or None)
    """
    pr_label = compliance_config.get("pr_label_format", "#PR")

    if content_type == "direct_promo":
        if pr_label not in text:
            return False, f"direct_promo投稿に {pr_label} がありません"
        # PR表記は冒頭付近にあるべき
        pr_pos = text.find(pr_label)
        if pr_pos > 10:
            return False, f"{pr_label} は投稿の冒頭に配置してください（現在位置: {pr_pos}）"

    return True, None


def check_char_count(text):
    """文字数制限をチェックする

    Xの文字カウント仕様:
    - 日本語（CJK）: 1文字 = 1文字としてカウント
    - URL: 23文字としてカウント（実際の長さに関わらず）
    - 改行: 1文字としてカウント

    Returns:
        tuple: (is_valid, char_count, error_message or None)
    """
    char_count = len(text)
    if char_count > MAX_TWEET_CHARS:
        return False, char_count, f"文字数超過: {char_count}/{MAX_TWEET_CHARS}"
    return True, char_count, None


def check_prohibited_phrases(text, prohibited_phrases):
    """禁止フレーズが含まれていないかチェックする

    Returns:
        tuple: (is_valid, found_phrases or [])
    """
    found = [phrase for phrase in prohibited_phrases if phrase in text]
    if found:
        return False, found
    return True, []


def check_duplicate(text, account_id=""):
    """投稿テキストの重複をチェックする

    ハッシュベースの重複検出。同じテキストが既に生成済みなら拒否する。

    Returns:
        tuple: (is_unique, error_message or None)
    """
    text_hash = hashlib.md5(f"{account_id}:{text}".encode()).hexdigest()
    if text_hash in _posted_hashes:
        return False, "重複投稿が検出されました"
    _posted_hashes.add(text_hash)
    return True, None


def clear_duplicate_cache():
    """重複検出キャッシュをクリアする（新しい月の生成時に使用）"""
    _posted_hashes.clear()


def validate_post(text, content_type, account_config):
    """投稿テキストを総合的にバリデーションする

    Args:
        text: 投稿テキスト
        content_type: コンテンツタイプ
        account_config: アカウントの設定辞書

    Returns:
        dict: {
            "is_valid": bool,
            "char_count": int,
            "errors": list[str],
            "warnings": list[str]
        }
    """
    errors = []
    warnings = []

    # 1. 文字数チェック
    char_valid, char_count, char_error = check_char_count(text)
    if not char_valid:
        errors.append(char_error)

    # 2. PR表記チェック
    compliance = account_config.get("compliance", {})
    pr_valid, pr_error = check_pr_label(text, content_type, compliance)
    if not pr_valid:
        errors.append(pr_error)

    # 3. 禁止フレーズチェック
    voice = account_config.get("voice", {})
    prohibited = voice.get("prohibited_phrases", [])
    phrase_valid, found_phrases = check_prohibited_phrases(text, prohibited)
    if not phrase_valid:
        errors.append(f"禁止フレーズが含まれています: {', '.join(found_phrases)}")

    # 4. 重複チェック
    account_id = account_config.get("account", {}).get("id", "")
    unique_valid, unique_error = check_duplicate(text, account_id)
    if not unique_valid:
        warnings.append(unique_error)

    # 5. 絵文字頻度チェック（警告のみ）
    emoji_freq = voice.get("emoji_frequency", "medium")
    emoji_count = sum(1 for c in text if ord(c) > 0x1F600)
    if emoji_freq == "low" and emoji_count > 2:
        warnings.append(f"絵文字が多すぎます（{emoji_count}個、推奨: 1-2個）")
    elif emoji_freq == "high" and emoji_count < 2:
        warnings.append(f"絵文字が少なすぎます（{emoji_count}個、推奨: 3-5個）")

    return {
        "is_valid": len(errors) == 0,
        "char_count": char_count,
        "errors": errors,
        "warnings": warnings,
    }
