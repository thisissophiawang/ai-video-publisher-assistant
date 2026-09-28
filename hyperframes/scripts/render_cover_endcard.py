from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "assets" / "input"
OUT = ROOT / "assets" / "cover"
W, H = 720, 1280
FONT = "/System/Library/Fonts/PingFang.ttc"


def font(size, bold=False):
    return ImageFont.truetype(FONT, size, index=8 if bold else 0)


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


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw, text, y, fnt, fill, stroke=0, stroke_fill=(36, 62, 86)):
    box = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    x = (W - (box[2] - box[0])) / 2
    draw.text((x, y), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def bg_from(path, blur=3, alpha=135):
    img = cover(Image.open(path).convert("RGB"), (W, H))
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    wash = Image.new("RGBA", (W, H), (177, 207, 229, alpha))
    return Image.alpha_composite(img.convert("RGBA"), wash).convert("RGB")


def cover_image():
    img = bg_from(INPUT / "reference_nyc_skyline.jpg", blur=2, alpha=110)
    d = ImageDraw.Draw(img, "RGBA")

    # Top identity chip
    rounded(d, (54, 70, 318, 132), 14, (36, 62, 86, 235))
    d.text((76, 83), "留学生 AI 求职", font=font(30, True), fill=(255, 255, 255))

    # Main title block
    rounded(d, (50, 238, 670, 620), 28, (248, 251, 253, 228))
    centered(d, "美国求职", 285, font(96, True), (23, 74, 110), stroke=1, stroke_fill=(255, 255, 255))
    centered(d, "别再手动改简历", 420, font(48, True), (36, 62, 86))
    centered(d, "用 AI 提升投递效率", 490, font(42, True), (23, 116, 184))

    # Columbia / NYC context card
    campus = cover(Image.open(INPUT / "reference_columbia_graduation.jpg").convert("RGB"), (560, 278))
    campus = campus.filter(ImageFilter.GaussianBlur(0.4))
    img.paste(campus, (80, 690))
    d.rectangle((80, 690, 640, 968), fill=(177, 207, 229, 55))
    rounded(d, (95, 710, 415, 765), 12, (36, 62, 86, 220))
    d.text((116, 721), "纽约 / 哥大背景", font=font(28, True), fill=(255, 255, 255))

    # Bottom feature pills
    pills = ["LinkedIn", "JD 分析", "Cover Letter", "模拟面试"]
    x, y = 58, 1040
    for i, p in enumerate(pills):
        w = [170, 165, 225, 175][i]
        rounded(d, (x, y, x + w, y + 54), 27, (58, 166, 161, 230))
        d.text((x + 22, y + 9), p, font=font(25, True), fill=(255, 255, 255))
        x += w + 12
        if x > 610:
            x, y = 120, 1110

    return img


def endcard_image():
    img = bg_from(INPUT / "reference_nyc_skyline.jpg", blur=6, alpha=150)
    d = ImageDraw.Draw(img, "RGBA")

    rounded(d, (64, 190, 656, 910), 34, (248, 251, 253, 238))
    centered(d, "立即尝试", 255, font(56, True), (36, 62, 86))
    centered(d, "用 AI 帮助你的求职", 335, font(44, True), (23, 116, 184))

    # App download visual
    rounded(d, (155, 455, 565, 560), 24, (21, 35, 48, 245))
    d.text((205, 482), "", font=font(44, True), fill=(255, 255, 255))
    d.text((255, 479), "Apple App 下载", font=font(34, True), fill=(255, 255, 255))

    rounded(d, (122, 635, 598, 755), 26, (235, 245, 250, 240), (160, 185, 200), 2)
    d.text((158, 666), "输入一句话", font=font(32, True), fill=(36, 62, 86))
    d.text((158, 710), "让 AI 帮你做求职内容", font=font(28, True), fill=(58, 166, 161))

    centered(d, "纽约留学生 AI 求职工具", 990, font(34, True), (255, 255, 255), stroke=3)
    centered(d, "LinkedIn · 简历 · JD · 面试", 1050, font(28, True), (255, 255, 255), stroke=2)

    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cover_image().save(OUT / "cover_us_job_search.jpg", quality=94)
    endcard_image().save(OUT / "endcard_apple_app_download.jpg", quality=94)


if __name__ == "__main__":
    main()
