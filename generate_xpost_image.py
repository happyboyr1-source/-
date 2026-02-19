#!/usr/bin/env python3
"""
X Post Style Image Generator
Generates comparison-style images matching the layout of @Akikun1124's anime OP posts.

Layout:
- Black background
- Multiple rows, each with: [Left Image] → [Right Image]
- Red arrow between images
- Anime title text (white with black outline) at top-right of each row
- Description text (large white with black outline) at bottom of each row
"""

from PIL import Image, ImageDraw, ImageFont
import os
import json

# === Configuration ===
OUTPUT_WIDTH = 1080
ROW_HEIGHT = 200
IMAGE_WIDTH = 440
IMAGE_HEIGHT = 170
ARROW_AREA_WIDTH = OUTPUT_WIDTH - IMAGE_WIDTH * 2  # space between images
PADDING_X = 30
PADDING_Y = 10
ROW_GAP = 8
FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

# Colors
BG_COLOR = (15, 15, 15)
ARROW_COLOR = (220, 40, 40)
TEXT_COLOR = (255, 255, 255)
OUTLINE_COLOR = (0, 0, 0)
TITLE_BG_COLOR = (0, 0, 0, 180)


def draw_outlined_text(draw, position, text, font, fill=TEXT_COLOR, outline=OUTLINE_COLOR, outline_width=3):
    """Draw text with outline/stroke effect."""
    x, y = position
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx * dx + dy * dy <= outline_width * outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    # Draw main text
    draw.text((x, y), text, font=font, fill=fill)


def draw_arrow(draw, x_start, y_center, arrow_width=60, arrow_height=40):
    """Draw a red right-pointing arrow."""
    # Arrow body (rectangle)
    body_height = arrow_height // 3
    body_width = arrow_width * 0.55
    draw.rectangle(
        [x_start, y_center - body_height // 2,
         x_start + body_width, y_center + body_height // 2],
        fill=ARROW_COLOR
    )
    # Arrow head (triangle)
    head_x = x_start + body_width
    draw.polygon([
        (head_x, y_center - arrow_height // 2),
        (head_x + arrow_width * 0.45, y_center),
        (head_x, y_center + arrow_height // 2),
    ], fill=ARROW_COLOR)


def load_and_resize_image(path, target_width, target_height, placeholder_label=""):
    """Load an image and resize it to fit within target dimensions, maintaining aspect ratio."""
    if not os.path.exists(path):
        # Create styled placeholder
        img = Image.new('RGB', (target_width, target_height), (40, 40, 50))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(FONT_PATH, 18)
            font_small = ImageFont.truetype(FONT_PATH, 13)
        except:
            font = ImageFont.load_default()
            font_small = font

        # Draw border
        draw.rectangle([0, 0, target_width - 1, target_height - 1], outline=(80, 80, 100), width=2)

        # Draw diagonal lines pattern
        for offset in range(-target_height, target_width, 30):
            draw.line([(offset, 0), (offset + target_height, target_height)], fill=(50, 50, 65), width=1)

        # Draw placeholder label
        if placeholder_label:
            bbox = draw.textbbox((0, 0), placeholder_label, font=font)
            tw = bbox[2] - bbox[0]
            tx = (target_width - tw) // 2
            ty = target_height // 2 - 20
            draw.rectangle([tx - 8, ty - 4, tx + tw + 8, ty + (bbox[3] - bbox[1]) + 8], fill=(0, 0, 0, 180))
            draw.text((tx, ty), placeholder_label, font=font, fill=(200, 200, 220))

        # Draw file path hint
        fname = os.path.basename(path)
        bbox2 = draw.textbbox((0, 0), fname, font=font_small)
        draw.text(((target_width - (bbox2[2] - bbox2[0])) // 2, target_height - 22),
                  fname, font=font_small, fill=(120, 120, 140))

        return img

    img = Image.open(path).convert('RGB')
    # Resize to fill the target area (crop to fit)
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        # Image is wider - fit height, crop width
        new_height = target_height
        new_width = int(target_height * img_ratio)
    else:
        # Image is taller - fit width, crop height
        new_width = target_width
        new_height = int(target_width / img_ratio)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Center crop
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    img = img.crop((left, top, left + target_width, top + target_height))

    return img


def generate_image(entries, output_path="output.png", title_header=None):
    """
    Generate the comparison image.

    entries: list of dicts with keys:
        - title: str (anime/work title, shown top-right)
        - description: str (explanation text, shown at bottom)
        - left_image: str (path to left image file)
        - right_image: str (path to right image file)

    title_header: optional header text at the very top of the image
    """
    num_rows = len(entries)

    # Calculate total height
    header_height = 80 if title_header else 0
    total_height = header_height + num_rows * ROW_HEIGHT + (num_rows - 1) * ROW_GAP + PADDING_Y * 2

    # Create canvas
    canvas = Image.new('RGB', (OUTPUT_WIDTH, total_height), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Load fonts
    try:
        font_title = ImageFont.truetype(FONT_PATH, 22)
        font_desc = ImageFont.truetype(FONT_PATH, 28)
        font_header = ImageFont.truetype(FONT_PATH, 32)
    except Exception as e:
        print(f"Font loading error: {e}, using default")
        font_title = ImageFont.load_default()
        font_desc = ImageFont.load_default()
        font_header = ImageFont.load_default()

    y_offset = PADDING_Y

    # Draw header if provided
    if title_header:
        # Header background
        draw.rectangle([0, 0, OUTPUT_WIDTH, header_height], fill=(25, 25, 25))
        bbox = draw.textbbox((0, 0), title_header, font=font_header)
        text_width = bbox[2] - bbox[0]
        header_x = (OUTPUT_WIDTH - text_width) // 2
        header_y = (header_height - (bbox[3] - bbox[1])) // 2
        draw_outlined_text(draw, (header_x, header_y), title_header, font_header,
                           fill=(255, 220, 50), outline_width=3)
        y_offset = header_height

    for i, entry in enumerate(entries):
        row_y = y_offset + i * (ROW_HEIGHT + ROW_GAP)

        # Calculate image positions
        left_x = PADDING_X
        left_y = row_y + (ROW_HEIGHT - IMAGE_HEIGHT) // 2 - 10
        right_x = OUTPUT_WIDTH - PADDING_X - IMAGE_WIDTH
        right_y = left_y

        # Load and paste images
        left_label = entry.get('left_label', '通常')
        right_label = entry.get('right_label', '崩壊')
        left_img = load_and_resize_image(entry.get('left_image', ''), IMAGE_WIDTH, IMAGE_HEIGHT, left_label)
        right_img = load_and_resize_image(entry.get('right_image', ''), IMAGE_WIDTH, IMAGE_HEIGHT, right_label)

        canvas.paste(left_img, (left_x, left_y))
        canvas.paste(right_img, (right_x, right_y))

        # Draw thin border around images
        for img_x, img_y in [(left_x, left_y), (right_x, right_y)]:
            draw.rectangle(
                [img_x - 1, img_y - 1, img_x + IMAGE_WIDTH, img_y + IMAGE_HEIGHT],
                outline=(80, 80, 80), width=1
            )

        # Draw arrow between images
        arrow_center_x = OUTPUT_WIDTH // 2 - 30
        arrow_center_y = left_y + IMAGE_HEIGHT // 2
        draw_arrow(draw, arrow_center_x, arrow_center_y, arrow_width=60, arrow_height=36)

        # Draw title text (top-right area of the row)
        title_text = entry.get('title', '')
        if title_text:
            title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
            title_w = title_bbox[2] - title_bbox[0]
            title_h = title_bbox[3] - title_bbox[1]
            title_x = right_x + IMAGE_WIDTH - title_w - 8
            title_y = right_y + 4

            # Semi-transparent background for title
            draw.rectangle(
                [title_x - 6, title_y - 2, title_x + title_w + 6, title_y + title_h + 4],
                fill=(0, 0, 0)
            )
            draw_outlined_text(draw, (title_x, title_y), title_text, font_title, outline_width=2)

        # Draw description text (bottom of row)
        desc_text = entry.get('description', '')
        if desc_text:
            desc_bbox = draw.textbbox((0, 0), desc_text, font=font_desc)
            desc_w = desc_bbox[2] - desc_bbox[0]
            desc_x = (OUTPUT_WIDTH - desc_w) // 2
            desc_y = row_y + ROW_HEIGHT - 38
            draw_outlined_text(draw, (desc_x, desc_y), desc_text, font_desc, outline_width=3)

        # Draw separator line between rows
        if i < num_rows - 1:
            sep_y = row_y + ROW_HEIGHT + ROW_GAP // 2
            draw.line([(20, sep_y), (OUTPUT_WIDTH - 20, sep_y)], fill=(50, 50, 50), width=1)

    # Save
    canvas.save(output_path, quality=95)
    print(f"Image saved to: {output_path}")
    print(f"Size: {canvas.width} x {canvas.height} px")
    return output_path


# === Generate: 作画崩壊まとめ ===
if __name__ == "__main__":
    """
    作画崩壊まとめ - 5 famous animation quality fails

    Each entry needs left_image (通常/before) and right_image (崩壊/after).
    Place your screenshot files in the images/ folder with matching filenames.

    Format: left = normal/good quality → right = 崩壊 (quality fail)
    """

    sakuga_entries = [
        {
            "title": "夜明け前より瑠璃色な",
            "description": "伝説のキャベツ",
            "left_image": "images/cabbage_normal.png",
            "right_image": "images/cabbage_houkai.png",
            "left_label": "普通のキャベツ",
            "right_label": "アニメ版キャベツ",
        },
        {
            "title": "DYNAMIC CHORD",
            "description": "歩かずにスライド移動する",
            "left_image": "images/dynachord_normal.png",
            "right_image": "images/dynachord_slide.png",
            "left_label": "通常の歩行",
            "right_label": "ダイナミック移動",
        },
        {
            "title": "七つの大罪 3期",
            "description": "1期と3期で別人になる",
            "left_image": "images/nanatsu_s1.png",
            "right_image": "images/nanatsu_s3.png",
            "left_label": "1期の作画",
            "right_label": "3期の作画",
        },
        {
            "title": "メルヘン・メドヘン",
            "description": "BD版で別アニメになる",
            "left_image": "images/marchen_tv.png",
            "right_image": "images/marchen_bd.png",
            "left_label": "TV放送版",
            "right_label": "BD修正版",
        },
        {
            "title": "いもいも",
            "description": "全話通して作画が限界突破",
            "left_image": "images/imoimo_novel.png",
            "right_image": "images/imoimo_anime.png",
            "left_label": "原作イラスト",
            "right_label": "アニメ版",
        },
    ]

    os.makedirs("images", exist_ok=True)
    generate_image(
        sakuga_entries,
        output_path="sakuga_houkai_matome.png",
        title_header="伝説のアニメ作画崩壊まとめ"
    )
