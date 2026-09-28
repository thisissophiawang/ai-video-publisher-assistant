from pathlib import Path
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
INPUT_IMAGE = ROOT / "assets" / "input" / "reference_linkedin_style.jpg"
OUTPUT_VIDEO = ROOT / "exports" / "study_abroad_ai_job_search_12s_720p.mp4"
PREVIEW_IMAGE = ROOT / "renders" / "study_abroad_ai_job_search_12s_720p_preview.jpg"
SUBTITLE_FILE = ROOT / "assets" / "subtitles" / "study_abroad_ai_job_search_12s.srt"
LOG_FILE = ROOT / "logs" / "study_abroad_ai_job_search_12s_720p.log"

W, H = 720, 1280
FPS = 30
DURATION = 12
TOTAL_FRAMES = FPS * DURATION

FONT = "/System/Library/Fonts/PingFang.ttc"


def font(size, bold=False):
    return ImageFont.truetype(FONT, size, index=8 if bold else 0)


def ease(x):
    return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, x)))


def text_size(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def paste_fit(base, img, box, alpha=255):
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    src = img.copy().convert("RGB")
    src_ratio = src.width / src.height
    dst_ratio = bw / bh
    if src_ratio > dst_ratio:
        new_h = bh
        new_w = int(new_h * src_ratio)
    else:
        new_w = bw
        new_h = int(new_w / src_ratio)
    src = src.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - bw) // 2
    top = (new_h - bh) // 2
    src = src.crop((left, top, left + bw, top + bh))
    if alpha < 255:
        src.putalpha(alpha)
        base.paste(src, (x1, y1), src)
    else:
        base.paste(src, (x1, y1))


def draw_centered(draw, text, y, fnt, fill, stroke_fill=None, stroke_width=0):
    tw, th = text_size(draw, text, fnt)
    draw.text(
        ((W - tw) / 2, y),
        text,
        font=fnt,
        fill=fill,
        stroke_fill=stroke_fill,
        stroke_width=stroke_width,
    )
    return y + th


def draw_banner(draw, text, y, fnt, fill=(255, 255, 255), bg=(58, 82, 106, 235)):
    tw, th = text_size(draw, text, fnt)
    pad_x, pad_y = 22, 10
    x = (W - tw) / 2
    rect = (x - pad_x, y - pad_y, x + tw + pad_x, y + th + pad_y)
    rounded_rect(draw, rect, 8, bg)
    draw.text((x, y), text, font=fnt, fill=fill)
    return rect


def draw_check_item(draw, text, y, alpha=255):
    bg = (62, 88, 112, alpha)
    rounded_rect(draw, (305, y, 650, y + 58), 6, bg)
    draw.text((325, y + 5), "✓", font=font(38, True), fill=(40, 56, 67, alpha))
    draw.text((375, y + 7), text, font=font(34, True), fill=(255, 255, 255, alpha))


def draw_mock_profile(draw):
    card_x, card_y, card_w, card_h = 72, 150, 576, 850
    rounded_rect(draw, (card_x, card_y, card_x + card_w, card_y + card_h), 4, (250, 252, 253), (218, 229, 238), 2)
    draw.rectangle((card_x, card_y, card_x + card_w, card_y + 160), fill=(236, 242, 247))
    draw.ellipse((118, 205, 292, 379), fill=(45, 88, 67))
    draw.ellipse((142, 230, 268, 356), fill=(232, 210, 188))
    draw.ellipse((156, 215, 254, 298), fill=(37, 42, 46))
    draw.rectangle((330, 214, 580, 228), fill=(186, 199, 210))
    draw.text((330, 245), "Data Analytics | Marketing | Strategy", font=font(21), fill=(48, 76, 93))
    draw.text((118, 520), "Business Analyst | Marketing Specialist", font=font(28), fill=(20, 20, 20))
    draw.text((118, 566), "MS in Applied Analytics", font=font(28), fill=(20, 20, 20))
    draw.text((118, 650), "Columbia University in New York", font=font(27), fill=(55, 55, 55))
    draw.text((118, 735), "500+ connections", font=font(29, True), fill=(16, 112, 184))
    rounded_rect(draw, (118, 792, 330, 850), 28, (10, 111, 190))
    draw.text((177, 802), "Open to", font=font(26, True), fill=(255, 255, 255))
    rounded_rect(draw, (350, 792, 565, 850), 28, (255, 255, 255), (170, 170, 170), 2)
    draw.text((392, 802), "Add section", font=font(25), fill=(70, 70, 70))


def draw_scene_overlay(draw, t):
    if t < 3:
        draw_banner(draw, "海外留学生求职", 86, font(38, True))
        draw_banner(draw, "别再手动改简历", 448, font(46, True))
        draw_check_item(draw, "JD 太多", 655, int(190 + 65 * ease(t / 3)))
        draw_check_item(draw, "简历难改", 735, int(150 + 105 * ease(t / 3)))
    elif t < 8:
        p = ease((t - 3) / 5)
        draw_banner(draw, "AI 求职效率流程", 86, font(38, True))
        items = ["分析 JD", "优化关键词", "生成 Cover Letter", "模拟英文面试"]
        base_y = 610
        for i, item in enumerate(items):
            item_alpha = 80 + int(175 * ease((p * 4 - i) / 1.2))
            draw_check_item(draw, item, base_y + i * 74, max(80, min(255, item_alpha)))
        rounded_rect(draw, (108, 1012, 612, 1088), 12, (255, 255, 255, 232))
        draw.text((135, 1032), "重复工作交给 AI", font=font(34, True), fill=(26, 76, 102))
    else:
        draw_banner(draw, "建立完整 LinkedIn 主页", 86, font(36, True))
        draw_check_item(draw, "有效社交", 610, 255)
        draw_check_item(draw, "提高竞争力", 690, 255)
        draw_check_item(draw, "扩大人际圈", 770, 255)
        draw_check_item(draw, "展现自我", 850, 255)
        rounded_rect(draw, (88, 1040, 632, 1130), 16, (255, 255, 255, 238))
        draw_centered(draw, "关注我：下一期搭 AI 求职流程", 1060, font(30, True), (23, 76, 104))


def make_frame(reference, idx):
    t = idx / FPS
    bg = Image.new("RGB", (W, H), (177, 207, 229))
    draw = ImageDraw.Draw(bg, "RGBA")

    if t < 3:
        scale = 1.0 + 0.03 * ease(t / 3)
        card_box = (68, 145, 652, 1052)
    elif t < 8:
        scale = 1.03 + 0.03 * ease((t - 3) / 5)
        card_box = (64, 138, 656, 1058)
    else:
        scale = 1.06 - 0.02 * ease((t - 8) / 4)
        card_box = (68, 145, 652, 1052)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow, "RGBA")
    rounded_rect(sd, (card_box[0] + 4, card_box[1] + 8, card_box[2] + 4, card_box[3] + 8), 8, (20, 40, 60, 42))
    bg = Image.alpha_composite(bg.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(bg, "RGBA")

    if INPUT_IMAGE.exists():
        ref = reference.copy().resize((int(reference.width * scale), int(reference.height * scale)), Image.LANCZOS)
        paste_fit(bg, ref, card_box, 210)
        overlay = Image.new("RGBA", (W, H), (255, 255, 255, 0))
        od = ImageDraw.Draw(overlay, "RGBA")
        rounded_rect(od, card_box, 6, (255, 255, 255, 72))
        bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(bg, "RGBA")
    else:
        draw_mock_profile(draw)

    draw_scene_overlay(draw, t)

    draw.rectangle((0, 1196, W, H), fill=(177, 207, 229, 255))
    draw.text((48, 1212), "720x1280 · 12s · AI求职效率", font=font(22), fill=(255, 255, 255, 210))
    return bg


def write_subtitles():
    SUBTITLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUBTITLE_FILE.write_text(
        """1
00:00:00,000 --> 00:00:03,000
海外留学生找工作，别再一个个手动改简历了。

2
00:00:03,000 --> 00:00:08,000
用 AI 分析 JD、优化简历关键词、生成 Cover Letter，还能模拟英文面试。

3
00:00:08,000 --> 00:00:12,000
把重复工作交给 AI，你把时间留给面试准备。
""",
        encoding="utf-8",
    )


def main():
    OUTPUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    reference = Image.open(INPUT_IMAGE).convert("RGB") if INPUT_IMAGE.exists() else Image.new("RGB", (1080, 1440), "white")
    writer = cv2.VideoWriter(str(OUTPUT_VIDEO), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    if not writer.isOpened():
        raise RuntimeError("Could not open MP4 writer")

    preview = None
    for idx in range(TOTAL_FRAMES):
        frame = make_frame(reference, idx)
        if idx == FPS * 2:
            preview = frame.copy()
        arr = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        writer.write(arr)
    writer.release()

    if preview:
        preview.save(PREVIEW_IMAGE, quality=92)
    write_subtitles()

    LOG_FILE.write_text(
        f"Generated {OUTPUT_VIDEO.name}\n"
        f"Spec: {W}x{H}, {DURATION}s, {FPS}fps, mp4\n"
        f"Reference image: {INPUT_IMAGE}\n"
        f"Subtitle file: {SUBTITLE_FILE}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
