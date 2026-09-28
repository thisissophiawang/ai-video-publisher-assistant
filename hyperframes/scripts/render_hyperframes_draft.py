from pathlib import Path
import math
import wave

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "input"
OUT = ROOT / "exports" / "study_abroad_ai_job_search_12s_720p_hyperframes_draft.mp4"
PREVIEW = ROOT / "renders" / "hyperframes_draft_preview.jpg"
SRT = ROOT / "assets" / "subtitles" / "study_abroad_ai_job_search_12s_final.srt"
SILENCE = ROOT / "assets" / "audio" / "study_abroad_ai_job_search_silent_placeholder.wav"
LOG = ROOT / "logs" / "hyperframes_draft_render.log"

W, H = 720, 1280
FPS = 30
DURATION = 12
FONT = "/System/Library/Fonts/PingFang.ttc"


def font(size, bold=False):
    return ImageFont.truetype(FONT, size, index=8 if bold else 0)


def ease(x):
    x = max(0, min(1, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def cover(img, size):
    tw, th = size
    r1 = img.width / img.height
    r2 = tw / th
    if r1 > r2:
        nh = th
        nw = int(nh * r1)
    else:
        nw = tw
        nh = int(nw / r1)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 2
    return img.crop((x, y, x + tw, y + th))


def rounded(draw, xy, r, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def text_center(draw, text, y, fnt, fill=(255, 255, 255), stroke=2):
    box = draw.textbbox((0, 0), text, font=fnt)
    x = (W - (box[2] - box[0])) / 2
    draw.text((x, y), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=(36, 62, 86))


def draw_caption(draw, lines):
    if isinstance(lines, str):
        lines = [lines]
    y = 900 if len(lines) == 1 else 860
    for line in lines:
        text_center(draw, line, y, font(48 if len(line) < 12 else 42, True), stroke=3)
        y += 62


def bg(path, blur=0, alpha=120):
    image = cover(Image.open(path).convert("RGB"), (W, H))
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(blur))
    overlay = Image.new("RGBA", (W, H), (177, 207, 229, alpha))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def label(draw, text, x=48, y=58):
    f = font(30, True)
    box = draw.textbbox((0, 0), text, font=f)
    rounded(draw, (x, y, x + box[2] + 28, y + box[3] + 22), 12, (42, 67, 89, 235))
    draw.text((x + 14, y + 8), text, font=f, fill=(255, 255, 255))


def progress_bar(draw, t):
    rounded(draw, (42, 1215, 678, 1230), 8, (255, 255, 255, 100))
    rounded(draw, (42, 1215, 42 + int(636 * t / DURATION), 1230), 8, (23, 116, 184, 210))


def frame_scene_1(local):
    img = bg(ASSETS / "reference_nyc_skyline.jpg", blur=0, alpha=100)
    d = ImageDraw.Draw(img, "RGBA")
    zoom = 1 + 0.03 * ease(local / 2)
    campus = cover(Image.open(ASSETS / "reference_columbia_graduation.jpg").convert("RGB"), (560, 330))
    campus = campus.resize((int(560 * zoom), int(330 * zoom)), Image.LANCZOS)
    img.paste(campus.crop((0, 0, 560, 330)), (80, 585))
    d.rectangle((80, 585, 640, 915), fill=(177, 207, 229, 80))
    label(d, "镜头01")
    text_center(d, "纽约留学生求职", 420, font(56, True), stroke=3)
    draw_caption(d, "在纽约读书找工作")
    progress_bar(d, local)
    return img


def frame_scene_2(local):
    img = bg(ASSETS / "reference_nyc_skyline.jpg", blur=5, alpha=150)
    d = ImageDraw.Draw(img, "RGBA")
    label(d, "镜头02")
    rounded(d, (62, 240, 658, 850), 24, (248, 251, 253, 235))
    d.text((100, 285), "Job Search Desktop", font=font(34, True), fill=(36, 62, 86))
    cards = [
        (96, 360, "Resume_v8.docx"),
        (260, 455, "Job Description"),
        (122, 560, "LinkedIn Profile"),
        (275, 665, "Recruiter Email"),
    ]
    for i, (x, y, title) in enumerate(cards):
        a = ease((local * 4 - i) / 1.2)
        dx = int((1 - a) * 80)
        rounded(d, (x + dx, y, x + dx + 345, y + 95), 14, (255, 255, 255, 245))
        d.text((x + dx + 18, y + 18), title, font=font(25, True), fill=(36, 62, 86))
        rounded(d, (x + dx + 18, y + 58, x + dx + 285, y + 72), 8, (180, 198, 211, 160))
    draw_caption(d, "别只靠手动改简历")
    progress_bar(d, 2 + local)
    return img


def frame_scene_3(local):
    img = Image.new("RGB", (W, H), (177, 207, 229))
    ref = cover(Image.open(ASSETS / "reference_linkedin_style.jpg").convert("RGB"), (560, 760))
    y0 = 180 - int(12 * ease(local / 2))
    img.paste(ref, (80, y0))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((80, y0, 640, y0 + 760), fill=(255, 255, 255, 60))
    label(d, "镜头03")
    text_center(d, "AI 优化 LinkedIn", 105, font(43, True), stroke=3)
    items = ["完善主页", "突出技能", "扩大人脉", "提升曝光"]
    for i, item in enumerate(items):
        a = ease((local * 3 - i) / 1.2)
        x = 320 + int((1 - a) * 120)
        y = 610 + i * 68
        rounded(d, (x, y, x + 310, y + 54), 9, (42, 67, 89, 235))
        d.text((x + 18, y + 4), "✓", font=font(34, True), fill=(24, 43, 58))
        d.text((x + 70, y + 8), item, font=font(30, True), fill=(255, 255, 255))
    draw_caption(d, "AI 优化 LinkedIn")
    progress_bar(d, 4 + local)
    return img


def frame_scene_4(local):
    img = bg(ASSETS / "reference_columbia_graduation.jpg", blur=5, alpha=160)
    d = ImageDraw.Draw(img, "RGBA")
    label(d, "镜头04")
    rounded(d, (52, 185, 668, 850), 24, (248, 251, 253, 235))
    d.text((82, 225), "AI 分析 JD / 优化关键词", font=font(38, True), fill=(36, 62, 86))
    rounded(d, (86, 300, 370, 705), 16, (255, 255, 255, 245))
    d.text((112, 328), "Job Description", font=font(27, True), fill=(36, 62, 86))
    for i in range(7):
        rounded(d, (112, 390 + i * 38, 335, 405 + i * 38), 8, (180, 198, 211, 160))
    rounded(d, (394, 300, 634, 705), 16, (255, 255, 255, 245))
    d.text((420, 328), "Keywords", font=font(27, True), fill=(36, 62, 86))
    for i, kw in enumerate(["Data", "SQL", "Marketing", "Strategy"]):
        a = ease((local * 4 - i) / 1.3)
        rounded(d, (420, 382 + i * 60, 604, 426 + i * 60), 22, (58, 166, 161, int(90 + 145 * a)))
        d.text((442, 390 + i * 60), kw, font=font(24, True), fill=(255, 255, 255))
    rounded(d, (112, 742, 604, 800), 12, (255, 242, 168, 220))
    d.text((136, 756), "Resume keywords highlighted", font=font(25, True), fill=(70, 72, 55))
    draw_caption(d, "分析 JD / 优化关键词")
    progress_bar(d, 6 + local)
    return img


def frame_scene_5(local):
    img = bg(ASSETS / "reference_columbia_graduation.jpg", blur=5, alpha=165)
    d = ImageDraw.Draw(img, "RGBA")
    label(d, "镜头05")
    rounded(d, (52, 190, 668, 845), 24, (248, 251, 253, 235))
    d.text((84, 230), "Cover Letter + 英文面试", font=font(38, True), fill=(36, 62, 86))
    rounded(d, (88, 315, 366, 730), 16, (255, 255, 255, 245))
    d.text((114, 345), "Cover Letter", font=font(27, True), fill=(36, 62, 86))
    for i in range(6):
        a = ease((local * 5 - i) / 1.3)
        rounded(d, (114, 410 + i * 45, 330, 427 + i * 45), 8, (180, 198, 211, int(60 + 130 * a)))
    rounded(d, (392, 315, 632, 730), 16, (255, 255, 255, 245))
    d.text((416, 345), "Mock Interview", font=font(24, True), fill=(36, 62, 86))
    for i, q in enumerate(["Tell me about yourself.", "Why this role?", "Your strength?"]):
        a = ease((local * 3 - i) / 1.2)
        rounded(d, (414, 410 + i * 82, 610, 468 + i * 82), 12, (42, 67, 89, int(80 + 155 * a)))
        d.text((428, 422 + i * 82), q, font=font(18, True), fill=(255, 255, 255))
    draw_caption(d, ["写 Cover Letter", "模拟英文面试"])
    progress_bar(d, 8 + local)
    return img


def frame_scene_6(local):
    img = bg(ASSETS / "reference_nyc_skyline.jpg", blur=5, alpha=145)
    d = ImageDraw.Draw(img, "RGBA")
    label(d, "镜头06")
    rounded(d, (64, 285, 656, 790), 26, (248, 251, 253, 242))
    d.text((104, 335), "AI 视频制作", font=font(42, True), fill=(36, 62, 86))
    rounded(d, (104, 425, 616, 555), 18, (235, 245, 250, 235), (160, 185, 200), 2)
    d.text((130, 455), "海外留学生怎么用 AI 提升求职效率", font=font(28, True), fill=(36, 62, 86))
    rounded(d, (220, 615, 500, 684), 34, (23, 116, 184, 255))
    text_center(d, "一键生成", 630, font(32, True), stroke=0)
    draw_caption(d, ["立即尝试", "用 AI 帮助你的求职"])
    progress_bar(d, 10 + local)
    return img


SCENES = [frame_scene_1, frame_scene_2, frame_scene_3, frame_scene_4, frame_scene_5, frame_scene_6]


def transition_blend(prev, curr, local_frame):
    # Last 5 frames of each 2s scene blend into the next scene.
    frames_per_scene = FPS * 2
    pos = local_frame % frames_per_scene
    if pos < frames_per_scene - 5:
        return curr
    scene_index = local_frame // frames_per_scene
    if scene_index >= len(SCENES) - 1:
        return curr
    alpha = (pos - (frames_per_scene - 5)) / 5
    nxt = SCENES[scene_index + 1]((pos - (frames_per_scene - 5)) / FPS)
    return Image.blend(curr, nxt, alpha)


def write_srt():
    SRT.parent.mkdir(parents=True, exist_ok=True)
    SRT.write_text(
        """1
00:00:00,250 --> 00:00:01,850
在纽约读书找工作

2
00:00:02,050 --> 00:00:03,750
别只靠手动改简历

3
00:00:04,050 --> 00:00:05,700
AI 优化 LinkedIn

4
00:00:06,050 --> 00:00:07,700
分析 JD / 优化关键词

5
00:00:08,050 --> 00:00:09,750
写 Cover Letter
模拟英文面试

6
00:00:10,050 --> 00:00:12,000
立即尝试
用 AI 帮助你的求职
""",
        encoding="utf-8",
    )


def write_silence():
    SILENCE.parent.mkdir(parents=True, exist_ok=True)
    rate = 44100
    with wave.open(str(SILENCE), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"\x00\x00" * rate * DURATION)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(OUT), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    if not writer.isOpened():
        raise RuntimeError("Could not open MP4 writer")
    preview = None
    total = FPS * DURATION
    for frame_idx in range(total):
        scene_index = min(frame_idx // (FPS * 2), len(SCENES) - 1)
        local = (frame_idx - scene_index * FPS * 2) / FPS
        frame = SCENES[scene_index](local)
        frame = transition_blend(None, frame, frame_idx)
        if frame_idx == 30:
            preview = frame.copy()
        writer.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))
    writer.release()
    if preview:
        preview.save(PREVIEW, quality=92)
    write_srt()
    write_silence()
    LOG.write_text(
        f"Rendered draft MP4: {OUT}\n"
        f"Spec: {W}x{H}, {DURATION}s, {FPS}fps\n"
        f"Subtitles: {SRT}\n"
        f"Silent placeholder audio: {SILENCE}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
