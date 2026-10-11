"""Explainer video + annotated cards for the write-up.

    python -m bench.video

Builds 1920x1080 slides (PIL), a voice-over per slide (Windows built-in text-to-speech), and
docs/video/erased_totals.mp4 (ffmpeg). The example cards are also saved to docs/figures/.
All numbers on the slides come from results/ (see the comments next to each slide).
"""

import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "video"
FIG = REPO / "docs" / "figures"
MAIN = REPO / "data" / "main" / "images"
CORD = REPO / "data" / "cord" / "images"

W, H = 1920, 1080
BG, INK, MUTED = (247, 245, 240), (29, 36, 51), (96, 104, 120)
RED, TEAL, AMBER, CARD = (209, 73, 91), (0, 121, 140), (214, 150, 40), (255, 255, 255)
FONTS = Path("C:/Windows/Fonts")


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    name = ("consolab.ttf" if bold else "consola.ttf") if mono else ("segoeuib.ttf" if bold else "segoeui.ttf")
    return ImageFont.truetype(str(FONTS / name), size)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def wrap(d: ImageDraw.ImageDraw, text: str, f, width: int) -> list[str]:
    lines = []
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            trial = f"{line} {word}".strip()
            if d.textlength(trial, font=f) <= width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def text(d, xy, s: str, f, fill=INK, width: int = 1700, gap: float = 1.25) -> int:
    x, y = xy
    for line in wrap(d, s, f, width):
        d.text((x, y), line, font=f, fill=fill)
        y += int(f.size * gap)
    return y


def paste_fit(img: Image.Image, path: Path, box: tuple[int, int, int, int], border: bool = True,
              crop: tuple[float, float, float, float] | None = None) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop((int(crop[0] * im.width), int(crop[1] * im.height), int(crop[2] * im.width), int(crop[3] * im.height)))
    scale = min((x1 - x0) / im.width, (y1 - y0) / im.height)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    x = x0 + ((x1 - x0) - im.width) // 2
    y = y0 + ((y1 - y0) - im.height) // 2
    if border:
        ImageDraw.Draw(img).rectangle((x - 3, y - 3, x + im.width + 2, y + im.height + 2), fill=(210, 206, 198))
    img.paste(im, (x, y))
    return x, y, x + im.width, y + im.height


def pill(d, xy, s: str, color, f) -> int:
    x, y = xy
    w = d.textlength(s, font=f) + 36
    d.rounded_rectangle((x, y, x + w, y + f.size + 22), radius=(f.size + 22) // 2, fill=color)
    d.text((x + 18, y + 8), s, font=f, fill=(255, 255, 255))
    return int(x + w)


def footer(d, s: str = "Erased Totals · Kaggle Benchmarking Challenge") -> None:
    d.text((80, H - 60), s, font=font(26), fill=MUTED)


# --------------------------------------------------------------------------- slides


def s_title():
    img, d = canvas()
    d.rectangle((0, 0, 24, H), fill=RED)
    y = text(d, (140, 300), "We taped over the total.", font(96, bold=True))
    y = text(d, (140, y + 10), "Vision models filled it in anyway.", font(96, bold=True), fill=RED)
    text(d, (140, y + 60), "A preregistered benchmark · 4 vision models · 528 bill images + 30 real receipts", font(40), fill=MUTED)
    footer(d)
    return img


def s_problem():
    img, d = canvas()
    paste_fit(img, MAIN / "main_b00_clean.jpg", (1080, 60, 1840, 1000))
    y = text(d, (100, 220), "Bills get shared as photos.", font(72, bold=True), width=900)
    text(d, (100, y + 40), "A thumb, a fold or a sticker covers part of the page, and then someone asks an assistant: \"What do I owe?\"",
         font(46), fill=MUTED, width=880)
    footer(d)
    return img


def s_four_answers():
    # results/main/scored.csv, item main_b00_N50, arm BASE.
    img, d = canvas()
    paste_fit(img, MAIN / "main_b00_N50.jpg", (60, 60, 820, 1000))
    y = text(d, (900, 90), "Half the total and one line are taped.", font(56, bold=True), width=960)
    y = text(d, (900, y + 10), "We asked four models for the total.", font(44), fill=MUTED, width=960)
    rows = [("Claude Sonnet 5", "215.61", "20"), ("Gemini 3 Flash", "230.61", "100"),
            ("Gemini 3.1 Flash-Lite", "211.61", "100"), ("GPT-5.4 nano", "0.61", "92")]
    y += 40
    for name, ans, conf in rows:
        d.rounded_rectangle((900, y, 1840, y + 120), radius=18, fill=CARD, outline=(225, 221, 212), width=2)
        d.text((935, y + 36), name, font=font(42), fill=INK)
        d.text((1400, y + 28), ans, font=font(56, bold=True, mono=True), fill=RED)
        pill(d, (1640, y + 36), f"conf {conf}", RED if int(conf) >= 70 else MUTED, font(28, bold=True))
        y += 140
    text(d, (900, y + 20), "True total: 255.61. With a line hidden, the right answer is \"can't tell\".", font(40, bold=True), fill=TEAL, width=960)
    footer(d)
    return img


def s_design():
    img, d = canvas()
    text(d, (80, 50), "Same bill, four versions (48 bills each)", font(60, bold=True))
    cols = [("main_b00_clean.jpg", "Nothing taped", "Answer: 255.61", INK),
            ("main_b00_D100.jpg", "Total taped, lines visible", "Answer: add the lines", INK),
            ("main_b00_N50.jpg", "Half total + one line taped", "Answer: can't tell", TEAL),
            ("main_b00_N100.jpg", "Total + one line taped", "Answer: can't tell", TEAL)]
    for i, (f, label, ans, color) in enumerate(cols):
        x0 = 60 + i * 465
        paste_fit(img, MAIN / f, (x0, 180, x0 + 430, 780), crop=(0.08, 0.43, 0.94, 0.85))
        text(d, (x0 + 10, 830), label, font(34, bold=True), width=420)
        text(d, (x0 + 10, 930), ans, font(34), fill=color, width=420)
    return img


def s_chart(path: Path, headline: str, sub: str = ""):
    img, d = canvas()
    y = text(d, (80, 50), headline, font(58, bold=True))
    if sub:
        text(d, (80, y), sub, font(38), fill=MUTED)
    paste_fit(img, path, (80, 220, W - 80, H - 90), border=False)
    footer(d)
    return img


def s_knows():
    # Gemini 3 Flash, main_b13_N100: PROBE visible=False computable=False; BASE 133.33 @ 100; TWOPASS UNREADABLE.
    img, d = canvas()
    paste_fit(img, MAIN / "main_b13_N100.jpg", (60, 60, 820, 1000))
    y = text(d, (900, 80), "Gemini 3 Flash knows the total is gone…", font(54, bold=True), width=960)
    y += 30
    d.rounded_rectangle((900, y, 1840, y + 230), radius=18, fill=CARD, outline=(225, 221, 212), width=2)
    d.text((935, y + 25), "Q: Is the total fully visible?", font=font(38), fill=INK)
    d.text((1600, y + 25), "No", font=font(38, bold=True), fill=TEAL)
    d.text((935, y + 95), "Q: Can it be computed from the", font=font(38), fill=INK)
    d.text((935, y + 145), "    visible amounts?", font=font(38), fill=INK)
    d.text((1600, y + 145), "No", font=font(38, bold=True), fill=TEAL)
    y += 280
    y = text(d, (900, y), "…yet asked for the total (fresh chat):", font(44, bold=True), width=960)
    d.rounded_rectangle((900, y + 10, 1840, y + 150), radius=18, fill=CARD, outline=(225, 221, 212), width=2)
    d.text((935, y + 45), "133.33", font=font(64, bold=True, mono=True), fill=RED)
    pill(d, (1250, y + 55), "confidence 100", RED, font(30, bold=True))
    text(d, (900, y + 190), "True total: 137.21, and it can't be known from this photo.", font(36), fill=MUTED, width=960)
    footer(d)
    return img


def s_real():
    # results/cord/scored.csv: Gemini 3 Flash, r00 N100 BASE -> "60.000" @ 95, truth 63.000. N100 invention 22/30.
    img, d = canvas()
    paste_fit(img, CORD / "cord_r00_N100.jpg", (60, 60, 760, 1000))
    y = text(d, (860, 90), "Real receipt photos: worse, not better", font(56, bold=True), width=1000)
    y = text(d, (860, y + 10), "30 photographed receipts (CORD, CC-BY 4.0), amounts taped the same way.", font(38), fill=MUTED, width=1000)
    y += 40
    d.rounded_rectangle((860, y, 1840, y + 150), radius=18, fill=CARD, outline=(225, 221, 212), width=2)
    d.text((895, y + 20), "Gemini 3 Flash, this receipt:", font=font(36), fill=INK)
    d.text((895, y + 70), "60.000", font=font(56, bold=True, mono=True), fill=RED)
    pill(d, (1180, y + 80), "confidence 95", RED, font(28, bold=True))
    d.text((1480, y + 85), "truth 63.000", font=font(34), fill=MUTED)
    y += 190
    for big, small in (("73%", "of hidden totals made up by Gemini 3 Flash (21% on synthetic bills)"),
                       ("30/30", "times its own probe said: hidden, not computable")):
        d.text((860, y), big, font=font(80, bold=True), fill=RED)
        text(d, (1160, y + 22), small, font(36), fill=INK, width=680)
        y += 150
    footer(d)
    return img


def s_takeaway():
    img, d = canvas()
    d.rectangle((0, 0, 24, H), fill=TEAL)
    y = text(d, (140, 200), "Ask whether the value is visible", font(80, bold=True))
    y = text(d, (140, y), "before asking for the value.", font(80, bold=True), fill=TEAL)
    y = text(d, (140, y + 40), "One extra turn took made-up totals from up to 73% down to 0–2%, "
             "without the strong models giving up on totals they could compute.", font(42), fill=MUTED, width=1640)
    text(d, (140, y + 60), "Benchmark:  kaggle.com/benchmarks/tasks/ainazu/erased-totals", font(38, mono=True), fill=INK)
    text(d, (140, y + 120), "Code + data: github.com/ainazulfiqar99acc/-erased-totals", font(38, mono=True), fill=INK)
    footer(d)
    return img


SLIDES = [
    ("01_title", s_title,
     "We taped over the total on a bill. Vision models filled it in anyway. Here is what we found."),
    ("02_problem", s_problem,
     "Bills and receipts get shared as phone photos. Often a thumb, a fold, or a sticker covers part of the page. "
     "Then someone asks an assistant: what do I owe?"),
    ("03_four_answers", s_four_answers,
     "Here, half the total and one line item are taped over. The right answer is: I can't tell. "
     "We asked four vision models. They gave four different totals, all ending in point six one. "
     "Gemini three Flash said two hundred thirty point six one, with one hundred percent confidence."),
    ("04_design", s_design,
     "The benchmark uses forty eight generated bills, so every answer key is exact. Each bill comes in versions: "
     "nothing taped, the total taped but the lines visible, and the total taped with one line hidden, "
     "where the only correct answer is: can't tell."),
    ("05_invention", lambda: s_chart(FIG / "invention.png", "Half a total is worse than no total",
                                     "With half the total visible, 92 to 100% of answers were made up"),
     "With the whole total hidden, the models made one up twenty one to seventy three percent of the time. "
     "Leave half the digits visible, and that jumps to ninety two to one hundred percent. The visible digits act as an anchor."),
    ("06_confidence", lambda: s_chart(FIG / "confidence.png", "How sure they say they are",
                                      "Gemini models: 95 on numbers they cannot see. Claude: 20."),
     "Confidence depends on the model. The Gemini models state ninety five on totals they cannot see. "
     "Claude guesses too, but says it is guessing, at around twenty."),
    ("07_knows", s_knows,
     "And they know. Asked separately, the strong models said every time that the total was hidden and could not be computed. "
     "Asked for the total, they still made one up."),
    ("08_real", s_real,
     "On thirty real receipt photos it got worse, not better. Gemini three Flash made up seventy three percent of hidden totals, at ninety five confidence."),
    ("09_fix", lambda: s_chart(FIG / "fix.png", "The fix: check first, then answer",
                               "Made-up totals fell to 0–2%; the strong models still computed recoverable totals"),
     "The fix is simple. Ask the model whether the total is visible, then ask for it. "
     "Made-up totals fell to zero to two percent, and the strong models still worked out totals they could compute."),
    ("10_takeaway", s_takeaway,
     "Ask whether the value is visible before asking for the value. The benchmark is on Kaggle, and all code and data are on GitHub."),
]

CARDS = {"03_four_answers": "card_four_answers.png", "04_design": "card_design.png",
         "07_knows": "card_knows_vs_does.png", "08_real": "card_real_receipt.png"}


def speak(text_: str, wav: Path) -> float:
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.SelectVoice('Microsoft Zira Desktop'); $s.Rate = 0; "
        f"$s.SetOutputToWaveFile('{wav}'); $s.Speak([Console]::In.ReadToEnd()); $s.Dispose()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], input=text_, text=True, check=True)
    with wave.open(str(wav)) as w:
        return w.getnframes() / w.getframerate()


def main() -> None:
    (OUT / "slides").mkdir(parents=True, exist_ok=True)
    (OUT / "audio").mkdir(parents=True, exist_ok=True)
    parts = []
    for key, build, narration in SLIDES:
        png = OUT / "slides" / f"{key}.png"
        build().save(png)
        if key in CARDS:
            Image.open(png).save(FIG / CARDS[key])
        wav = OUT / "audio" / f"{key}.wav"
        dur = speak(narration, wav) + 0.8
        clip = OUT / "audio" / f"{key}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(png), "-i", str(wav),
            "-af", "apad", "-t", f"{dur:.2f}", "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-r", "30", "-c:a", "aac", "-ar", "44100", "-ac", "1", "-b:a", "128k", str(clip),
        ], check=True)
        parts.append(clip)
        print(f"{key}: {dur:.1f}s")
    listing = OUT / "audio" / "parts.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    final = OUT / "erased_totals.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", "-movflags", "+faststart", str(final)], check=True)
    print("wrote", final, f"{final.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
