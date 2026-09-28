from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "renders" / "storyboards"
INPUT = ROOT / "assets" / "input"
W, H = 720, 1280
FONT = "/System/Library/Fonts/PingFang.ttc"


def font(size, bold=False):
    return ImageFont.truetype(FONT, size, index=8 if bold else 0)


def fit_cover(img, size):
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


def wrap_text(draw, text, fnt, max_width):
    lines = []
    current = ""
    for char in text:
        test = current + char
        if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def text_center(draw, text, y, fnt, fill, stroke=0):
    box = draw.textbbox((0, 0), text, font=fnt)
    x = (W - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=(35, 55, 75))


def panel(draw, xy, fill=(255, 255, 255, 230), radius=18):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def label(draw, text, xy, color=(55, 82, 106, 235), size=30):
    x, y = xy
    f = font(size, True)
    box = draw.textbbox((0, 0), text, font=f)
    draw.rounded_rectangle((x, y, x + box[2] + 30, y + box[3] + 22), radius=10, fill=color)
    draw.text((x + 15, y + 8), text, font=f, fill=(255, 255, 255))


def base(bg_path=None, blur=False):
    if bg_path and bg_path.exists():
        img = fit_cover(Image.open(bg_path).convert("RGB"), (W, H))
        if blur:
            img = img.filter(ImageFilter.GaussianBlur(4))
        tint = Image.new("RGBA", (W, H), (177, 207, 229, 120))
        img = Image.alpha_composite(img.convert("RGBA"), tint).convert("RGB")
    else:
        img = Image.new("RGB", (W, H), (177, 207, 229))
    return img


def footer(draw, shot, time, transition):
    panel(draw, (40, 1120, 680, 1238), (38, 61, 82, 225), 16)
    draw.text((62, 1138), f"{shot}  {time}", font=font(28, True), fill=(255, 255, 255))
    lines = wrap_text(draw, f"转场：{transition}", font(22), 570)
    y = 1183
    for line in lines[:2]:
        draw.text((62, y), line, font=font(22), fill=(232, 241, 248))
        y += 28


def draw_laptop(draw, x, y, w, h, title="AI Assistant"):
    draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=(245, 249, 252), outline=(170, 190, 205), width=2)
    draw.rectangle((x, y, x + w, y + 54), fill=(224, 236, 245))
    draw.text((x + 22, y + 14), title, font=font(24, True), fill=(45, 72, 94))


def scene_01():
    img = base(INPUT / "reference_nyc_skyline.jpg", blur=False)
    d = ImageDraw.Draw(img, "RGBA")
    panel(d, (60, 130, 660, 1045), (255, 255, 255, 70), 24)
    columbia = fit_cover(Image.open(INPUT / "reference_columbia_graduation.jpg").convert("RGB"), (560, 320))
    img.paste(columbia, (80, 575))
    d.rectangle((80, 575, 640, 895), fill=(177, 207, 229, 80))
    label(d, "镜头01", (54, 58))
    text_center(d, "纽约留学生求职", 420, font(52, True), (255, 255, 255), 2)
    text_center(d, "在纽约读书找工作", 500, font(34, True), (255, 255, 255), 1)
    footer(d, "镜头01", "00:00-00:02", "从纽约/哥大背景推近到电脑屏幕")
    return img


def scene_02():
    img = base(INPUT / "reference_nyc_skyline.jpg", blur=True)
    d = ImageDraw.Draw(img, "RGBA")
    label(d, "镜头02", (54, 58))
    draw_laptop(d, 70, 260, 580, 620, "Job Search Desktop")
    cards = [
        (105, 345, 405, 470, "Resume_v8.docx"),
        (250, 430, 600, 565, "Job Description"),
        (120, 555, 530, 690, "LinkedIn Profile"),
        (260, 680, 610, 815, "Recruiter Email"),
    ]
    for x1, y1, x2, y2, title in cards:
        panel(d, (x1, y1, x2, y2), (255, 255, 255, 235), 12)
        d.text((x1 + 18, y1 + 18), title, font=font(25, True), fill=(40, 65, 84))
        d.line((x1 + 18, y1 + 62, x2 - 18, y1 + 62), fill=(210, 220, 228), width=2)
        d.text((x1 + 18, y1 + 78), "manual edits...", font=font(22), fill=(100, 110, 120))
    text_center(d, "别只靠手动改简历", 930, font(46, True), (255, 255, 255), 2)
    footer(d, "镜头02", "00:02-00:04", "点击 LinkedIn 页面，放大进入主页优化")
    return img


def scene_03():
    img = base(None)
    ref = fit_cover(Image.open(INPUT / "reference_linkedin_style.jpg").convert("RGB"), (560, 730))
    img.paste(ref, (80, 185))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((80, 185, 640, 915), fill=(255, 255, 255, 60))
    label(d, "镜头03", (54, 58))
    text_center(d, "AI 优化 LinkedIn", 105, font(44, True), (255, 255, 255), 2)
    items = ["完善主页", "突出技能", "扩大人脉", "提升曝光"]
    y = 610
    for item in items:
        d.rounded_rectangle((310, y, 630, y + 56), radius=8, fill=(58, 82, 106, 230))
        d.text((330, y + 5), "✓", font=font(36, True), fill=(30, 45, 58))
        d.text((382, y + 9), item, font=font(31, True), fill=(255, 255, 255))
        y += 70
    footer(d, "镜头03", "00:04-00:06", "技能关键词横向滑动，变成 JD 关键词标签")
    return img


def scene_04():
    img = base(INPUT / "reference_columbia_graduation.jpg", blur=True)
    d = ImageDraw.Draw(img, "RGBA")
    label(d, "镜头04", (54, 58))
    panel(d, (55, 180, 665, 950), (244, 249, 252, 240), 18)
    d.text((85, 215), "AI 分析 JD / 优化关键词", font=font(38, True), fill=(35, 70, 95))
    panel(d, (85, 290, 365, 720), (255, 255, 255, 245), 12)
    d.text((110, 320), "Job Description", font=font(28, True), fill=(40, 65, 84))
    for i in range(7):
        d.rounded_rectangle((110, 380 + i * 42, 335, 400 + i * 42), radius=4, fill=(180, 198, 211, 180))
    panel(d, (390, 290, 635, 720), (255, 255, 255, 245), 12)
    d.text((415, 320), "Keywords", font=font(28, True), fill=(40, 65, 84))
    for i, kw in enumerate(["Data", "SQL", "Strategy", "Marketing"]):
        d.rounded_rectangle((415, 375 + i * 60, 600, 420 + i * 60), radius=22, fill=(60, 140, 165, 225))
        d.text((440, 382 + i * 60), kw, font=font(25, True), fill=(255, 255, 255))
    d.rounded_rectangle((110, 770, 600, 825), radius=10, fill=(255, 244, 160, 210))
    d.text((135, 782), "Resume keywords highlighted", font=font(25, True), fill=(70, 72, 55))
    footer(d, "镜头04", "00:06-00:08", "关键词聚合，变成 Cover Letter 文档标题")
    return img


def scene_05():
    img = base(INPUT / "reference_columbia_graduation.jpg", blur=True)
    d = ImageDraw.Draw(img, "RGBA")
    label(d, "镜头05", (54, 58))
    panel(d, (55, 175, 665, 940), (245, 250, 253, 240), 20)
    d.text((82, 210), "Cover Letter + 英文面试", font=font(38, True), fill=(35, 70, 95))
    panel(d, (90, 300, 365, 760), (255, 255, 255, 245), 14)
    d.text((115, 330), "Cover Letter", font=font(27, True), fill=(40, 65, 84))
    for i in range(6):
        d.rounded_rectangle((115, 392 + i * 48, 335, 414 + i * 48), radius=4, fill=(188, 205, 216, 170))
    panel(d, (390, 300, 635, 760), (255, 255, 255, 245), 14)
    d.text((415, 330), "Mock Interview", font=font(25, True), fill=(40, 65, 84))
    qs = ["Tell me about yourself.", "Why this role?", "Your strength?"]
    for i, q in enumerate(qs):
        d.rounded_rectangle((415, 392 + i * 86, 610, 452 + i * 86), radius=10, fill=(58, 82, 106, 225))
        d.text((430, 404 + i * 86), q, font=font(19, True), fill=(255, 255, 255))
    text_center(d, "写 Cover Letter  模拟英文面试", 845, font(34, True), (255, 255, 255), 2)
    footer(d, "镜头05", "00:08-00:10", "面试卡片收束，变成一句话输入框")
    return img


def scene_06():
    img = base(INPUT / "reference_nyc_skyline.jpg", blur=True)
    d = ImageDraw.Draw(img, "RGBA")
    label(d, "镜头06", (54, 58))
    panel(d, (65, 295, 655, 785), (255, 255, 255, 242), 26)
    d.text((105, 340), "AI 视频制作", font=font(40, True), fill=(35, 70, 95))
    d.rounded_rectangle((105, 425, 615, 555), radius=18, fill=(238, 245, 249), outline=(170, 195, 210), width=2)
    prompt = "海外留学生怎么用 AI 提升求职效率"
    lines = wrap_text(d, prompt, font(30, True), 450)
    y = 452
    for line in lines:
        d.text((130, y), line, font=font(30, True), fill=(45, 70, 90))
        y += 42
    d.rounded_rectangle((220, 610, 500, 680), radius=35, fill=(30, 118, 185))
    text_center(d, "一键生成", 624, font(31, True), (255, 255, 255))
    text_center(d, "立即尝试", 840, font(52, True), (255, 255, 255), 2)
    text_center(d, "用 AI 帮助你的求职", 915, font(40, True), (255, 255, 255), 2)
    footer(d, "镜头06", "00:10-00:12", "最终镜头定格 0.5 秒，无下一镜")
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    scenes = [scene_01, scene_02, scene_03, scene_04, scene_05, scene_06]
    for i, make in enumerate(scenes, 1):
        img = make()
        img.save(OUT / f"shot_{i:02d}.jpg", quality=92)


if __name__ == "__main__":
    main()
