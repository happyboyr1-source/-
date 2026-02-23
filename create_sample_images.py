#!/usr/bin/env python3
"""
Generate representative sample images for 作画崩壊まとめ entries.
Creates stylized illustrations that convey the concept of each animation quality fail.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import random
import math

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
W, H = 440, 170

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()


def draw_gradient_bg(draw, w, h, color_top, color_bottom):
    """Draw a vertical gradient background."""
    for y in range(h):
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * y / h)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * y / h)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def draw_cabbage(draw, cx, cy, radius, quality="good"):
    """Draw a cabbage - good version is round with leaf details, bad is a plain circle."""
    if quality == "good":
        # Nice layered cabbage with leaf veins
        colors = [(60, 140, 50), (70, 160, 55), (80, 180, 60), (100, 200, 70), (120, 210, 90)]
        for i, c in enumerate(colors):
            r = radius - i * (radius // 6)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
        # Leaf veins
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = cx + int(radius * 0.2 * math.cos(rad))
            y1 = cy + int(radius * 0.2 * math.sin(rad))
            x2 = cx + int(radius * 0.8 * math.cos(rad))
            y2 = cy + int(radius * 0.8 * math.sin(rad))
            draw.line([(x1, y1), (x2, y2)], fill=(50, 130, 40), width=2)
        # Highlight
        draw.ellipse([cx - radius//4, cy - radius//3, cx + radius//6, cy - radius//6],
                     fill=(140, 230, 110))
    else:
        # Infamous bad cabbage - just a green sphere/ball with no detail
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(80, 200, 80))
        # Single awkward line
        draw.arc([cx - radius, cy - radius, cx + radius, cy + radius], 0, 180, fill=(60, 170, 60), width=3)
        # It looks like a ball, not a cabbage - that's the point


def draw_character_silhouette(draw, cx, cy, scale=1.0, quality="good", color=(200, 180, 160)):
    """Draw a simple anime character silhouette."""
    s = scale
    # Head center is above the body reference point
    head_cy = cy - int(45 * s)
    head_r = int(15 * s)
    draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], fill=color)

    if quality == "good":
        # Nice proportioned body
        # Neck
        neck_top = head_cy + head_r
        neck_bot = neck_top + int(8 * s)
        draw.rectangle([cx - int(4*s), neck_top, cx + int(4*s), neck_bot], fill=color)
        # Body (torso)
        body_top = neck_bot
        body_bot = cy + int(10*s)
        draw.polygon([
            (cx - int(18*s), body_top),
            (cx + int(18*s), body_top),
            (cx + int(14*s), body_bot),
            (cx - int(14*s), body_bot),
        ], fill=color)
        # Arms
        draw.line([(cx - int(18*s), body_top + int(5*s)), (cx - int(30*s), cy)], fill=color, width=max(int(5*s), 1))
        draw.line([(cx + int(18*s), body_top + int(5*s)), (cx + int(30*s), cy)], fill=color, width=max(int(5*s), 1))
        # Legs
        draw.line([(cx - int(8*s), body_bot), (cx - int(12*s), cy + int(40*s))], fill=color, width=max(int(6*s), 1))
        draw.line([(cx + int(8*s), body_bot), (cx + int(12*s), cy + int(40*s))], fill=color, width=max(int(6*s), 1))
        # Eyes (detailed)
        ey = head_cy - int(3*s)
        draw.ellipse([cx - int(9*s), ey - int(4*s), cx - int(2*s), ey + int(4*s)], fill=(80, 80, 180))
        draw.ellipse([cx + int(2*s), ey - int(4*s), cx + int(9*s), ey + int(4*s)], fill=(80, 80, 180))
        # Hair
        for angle in range(-60, 61, 15):
            rad = math.radians(angle - 90)
            hx = cx + int((head_r + 4) * math.cos(rad))
            hy = head_cy + int((head_r + 4) * math.sin(rad))
            draw.line([(cx, head_cy - head_r), (hx, hy)], fill=(60, 40, 30), width=max(int(2*s), 1))
    else:
        # Poorly drawn - wrong proportions, wobbly lines
        neck_top = head_cy + head_r
        body_bot = cy + int(12*s)
        # Misshapen body
        draw.polygon([
            (cx - int(22*s), neck_top + int(2*s)),
            (cx + int(16*s), neck_top - int(2*s)),
            (cx + int(20*s), body_bot),
            (cx - int(16*s), body_bot - int(4*s)),
        ], fill=color)
        # Wonky arms
        draw.line([(cx - int(22*s), neck_top + int(8*s)), (cx - int(38*s), cy + int(5*s))], fill=color, width=max(int(7*s), 1))
        draw.line([(cx + int(16*s), neck_top + int(8*s)), (cx + int(35*s), cy + int(10*s))], fill=color, width=max(int(3*s), 1))
        # Uneven legs
        draw.line([(cx - int(6*s), body_bot), (cx - int(18*s), cy + int(40*s))], fill=color, width=max(int(8*s), 1))
        draw.line([(cx + int(6*s), body_bot), (cx + int(4*s), cy + int(38*s))], fill=color, width=max(int(4*s), 1))
        # Derpy eyes
        ey = head_cy - int(2*s)
        draw.ellipse([cx - int(10*s), ey - int(5*s), cx - int(1*s), ey + int(3*s)], fill=(80, 80, 180))
        draw.ellipse([cx + int(4*s), ey - int(3*s), cx + int(11*s), ey + int(4*s)], fill=(80, 80, 180))


def create_scene_bg(w, h, scene="indoor"):
    """Create a simple anime scene background."""
    img = Image.new('RGB', (w, h))
    draw = ImageDraw.Draw(img)

    if scene == "kitchen":
        draw_gradient_bg(draw, w, h, (180, 170, 150), (140, 130, 110))
        # Counter
        draw.rectangle([0, h * 2 // 3, w, h], fill=(120, 90, 60))
        draw.line([(0, h * 2 // 3), (w, h * 2 // 3)], fill=(100, 70, 40), width=3)
    elif scene == "outdoor":
        draw_gradient_bg(draw, w, h, (100, 160, 220), (150, 200, 240))
        # Ground
        draw.rectangle([0, h * 3 // 4, w, h], fill=(80, 140, 60))
    elif scene == "street":
        draw_gradient_bg(draw, w, h, (150, 170, 200), (120, 130, 150))
        # Road
        draw.rectangle([0, h * 2 // 3, w, h], fill=(100, 100, 105))
        draw.line([(0, h * 5 // 6), (w, h * 5 // 6)], fill=(180, 180, 60), width=2)
    elif scene == "stage":
        draw_gradient_bg(draw, w, h, (40, 20, 60), (20, 10, 40))
        # Stage floor
        draw.rectangle([0, h * 3 // 4, w, h], fill=(60, 40, 30))
    elif scene == "school":
        draw_gradient_bg(draw, w, h, (200, 195, 180), (180, 175, 160))
        # Desk
        draw.rectangle([30, h // 2, w - 30, h // 2 + 8], fill=(160, 120, 70))
    else:
        draw_gradient_bg(draw, w, h, (60, 60, 80), (40, 40, 55))

    return img, draw


def make_cabbage_normal():
    img, draw = create_scene_bg(W, H, "kitchen")
    # Plate
    draw.ellipse([W//2 - 60, H//2 - 10, W//2 + 60, H//2 + 50], fill=(230, 230, 230))
    draw.ellipse([W//2 - 55, H//2 - 5, W//2 + 55, H//2 + 45], fill=(245, 245, 245))
    # Good cabbage on plate
    draw_cabbage(draw, W//2, H//2 + 5, 35, "good")
    # Label
    font = get_font(14)
    draw.text((10, H - 25), "通常の作画", font=font, fill=(255, 255, 255))
    return img


def make_cabbage_houkai():
    img, draw = create_scene_bg(W, H, "kitchen")
    # Plate
    draw.ellipse([W//2 - 60, H//2 - 10, W//2 + 60, H//2 + 50], fill=(230, 230, 230))
    draw.ellipse([W//2 - 55, H//2 - 5, W//2 + 55, H//2 + 45], fill=(245, 245, 245))
    # Bad cabbage - just a green ball
    draw_cabbage(draw, W//2, H//2 + 5, 35, "bad")
    # Add a "!" mark for emphasis
    font = get_font(24)
    draw.text((W - 50, 10), "!?", font=font, fill=(255, 50, 50))
    font = get_font(14)
    draw.text((10, H - 25), "作画崩壊", font=font, fill=(255, 100, 100))
    return img


def make_dynachord_normal():
    img, draw = create_scene_bg(W, H, "street")
    # Character walking normally with visible walking pose
    draw_character_silhouette(draw, W//3, H//2 + 20, scale=1.2, quality="good", color=(180, 150, 200))
    # Walking motion lines
    for i in range(3):
        y = H//2 + 30 + i * 8
        draw.line([(W//3 - 50 - i*10, y), (W//3 - 20, y)], fill=(200, 200, 200, 100), width=1)
    # Another character
    draw_character_silhouette(draw, W * 2//3, H//2 + 20, scale=1.1, quality="good", color=(200, 170, 150))
    font = get_font(14)
    draw.text((10, H - 25), "普通に歩いている", font=font, fill=(255, 255, 255))
    return img


def make_dynachord_slide():
    img, draw = create_scene_bg(W, H, "street")
    # Character in stiff pose "sliding"
    draw_character_silhouette(draw, W//3, H//2 + 20, scale=1.2, quality="bad", color=(180, 150, 200))
    # Slide effect lines (horizontal speed lines)
    for i in range(6):
        y = H//2 + i * 12 - 10
        draw.line([(W//3 - 80, y), (W//3 + 80, y)], fill=(255, 255, 100), width=1)
    # Arrow showing sliding direction
    draw.polygon([(W//3 + 60, H//2 + 10), (W//3 + 90, H//2 + 20), (W//3 + 60, H//2 + 30)],
                 fill=(255, 255, 0))
    # Stiff character
    draw_character_silhouette(draw, W * 2//3, H//2 + 20, scale=1.1, quality="bad", color=(200, 170, 150))
    font = get_font(14)
    draw.text((10, H - 25), "スライド移動！", font=font, fill=(255, 100, 100))
    return img


def make_nanatsu_s1():
    img, draw = create_scene_bg(W, H, "outdoor")
    # Good quality character - heroic pose
    draw_character_silhouette(draw, W//2, H//2 + 10, scale=1.4, quality="good", color=(220, 190, 160))
    # Battle aura effect
    for r in range(50, 80, 10):
        draw.ellipse([W//2 - r, H//2 + 10 - r, W//2 + r, H//2 + 10 + r],
                     outline=(255, 200, 50, 80), width=1)
    font = get_font(14)
    draw.text((10, H - 25), "1期 A-1 Pictures", font=font, fill=(255, 255, 255))
    # Quality badge
    font_sm = get_font(12)
    draw.rectangle([W - 80, 5, W - 5, 25], fill=(0, 100, 200))
    draw.text((W - 75, 7), "高品質", font=font_sm, fill=(255, 255, 255))
    return img


def make_nanatsu_s3():
    img, draw = create_scene_bg(W, H, "outdoor")
    # Bad quality character - same pose but poorly drawn
    draw_character_silhouette(draw, W//2, H//2 + 10, scale=1.4, quality="bad", color=(220, 190, 160))
    font = get_font(14)
    draw.text((10, H - 25), "3期 スタジオディーン", font=font, fill=(255, 100, 100))
    # Quality badge
    font_sm = get_font(12)
    draw.rectangle([W - 80, 5, W - 5, 25], fill=(200, 50, 50))
    draw.text((W - 75, 7), "作画崩壊", font=font_sm, fill=(255, 255, 255))
    return img


def make_marchen_tv():
    img, draw = create_scene_bg(W, H, "school")
    # TV broadcast - character with poor quality
    draw_character_silhouette(draw, W//2, H//2 + 15, scale=1.3, quality="bad", color=(200, 160, 180))
    font = get_font(14)
    draw.text((10, H - 25), "TV放送版", font=font, fill=(255, 100, 100))
    # TV icon
    draw.rectangle([W - 60, 8, W - 10, 32], outline=(255, 255, 255), width=2)
    font_sm = get_font(10)
    draw.text((W - 55, 12), "TV", font=font_sm, fill=(255, 255, 255))
    return img


def make_marchen_bd():
    img, draw = create_scene_bg(W, H, "school")
    # BD version - completely redrawn, good quality
    draw_character_silhouette(draw, W//2, H//2 + 15, scale=1.3, quality="good", color=(200, 160, 180))
    font = get_font(14)
    draw.text((10, H - 25), "BD修正版（別アニメ）", font=font, fill=(100, 200, 255))
    # BD disc icon
    draw.ellipse([W - 45, 8, W - 10, 43], outline=(100, 200, 255), width=2)
    draw.ellipse([W - 33, 20, W - 22, 31], outline=(100, 200, 255), width=1)
    font_sm = get_font(10)
    draw.text((W - 55, 12), "BD", font=font_sm, fill=(100, 200, 255))
    # Sparkle effects showing improvement
    for _ in range(5):
        sx = random.randint(50, W - 50)
        sy = random.randint(20, H - 40)
        draw.text((sx, sy), "✦", font=get_font(12), fill=(255, 255, 200))
    return img


def make_imoimo_novel():
    img, draw = create_scene_bg(W, H, "indoor")
    # Light novel illustration style - good quality
    draw_character_silhouette(draw, W//3 + 20, H//2 + 10, scale=1.3, quality="good", color=(230, 200, 190))
    # Second character
    draw_character_silhouette(draw, W * 2//3 - 20, H//2 + 10, scale=1.2, quality="good", color=(200, 180, 220))
    font = get_font(14)
    draw.text((10, H - 25), "原作ラノベイラスト", font=font, fill=(255, 255, 255))
    # Book icon
    draw.rectangle([W - 50, 8, W - 10, 35], fill=(200, 180, 140))
    draw.line([(W - 30, 8), (W - 30, 35)], fill=(160, 140, 100), width=2)
    return img


def make_imoimo_anime():
    img, draw = create_scene_bg(W, H, "indoor")
    # Anime version - completely broken
    draw_character_silhouette(draw, W//3 + 20, H//2 + 10, scale=1.3, quality="bad", color=(230, 200, 190))
    draw_character_silhouette(draw, W * 2//3 - 20, H//2 + 10, scale=1.2, quality="bad", color=(200, 180, 220))
    font = get_font(14)
    draw.text((10, H - 25), "アニメ版（全話崩壊）", font=font, fill=(255, 100, 100))
    # Warning marks
    font_lg = get_font(28)
    draw.text((W - 60, 5), "!!", font=font_lg, fill=(255, 50, 50))
    return img


if __name__ == "__main__":
    random.seed(42)  # Reproducible output
    os.makedirs("images", exist_ok=True)

    pairs = [
        ("images/cabbage_normal.png", make_cabbage_normal),
        ("images/cabbage_houkai.png", make_cabbage_houkai),
        ("images/dynachord_normal.png", make_dynachord_normal),
        ("images/dynachord_slide.png", make_dynachord_slide),
        ("images/nanatsu_s1.png", make_nanatsu_s1),
        ("images/nanatsu_s3.png", make_nanatsu_s3),
        ("images/marchen_tv.png", make_marchen_tv),
        ("images/marchen_bd.png", make_marchen_bd),
        ("images/imoimo_novel.png", make_imoimo_novel),
        ("images/imoimo_anime.png", make_imoimo_anime),
    ]

    for path, func in pairs:
        img = func()
        img.save(path, quality=95)
        print(f"Created: {path}")

    print(f"\nAll {len(pairs)} images created successfully!")
