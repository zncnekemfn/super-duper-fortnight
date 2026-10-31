"""
Generador de vídeos verticales (1080x1920) para ofertas de Amazon.
Pensado para el VPS del bot: solo usa Pillow, numpy y ffmpeg.

Uso:
    from offer_video import make_offer_video
    make_offer_video(
        title="Nintendo Switch 2 Cámara HD con micrófono",
        image="https://m.media-amazon.com/images/I/xxxx.jpg",  # o ruta local
        price=20.90, old_price=59.99,
        out="oferta.mp4",
        badge="MÍNIMO HISTÓRICO",   # opcional
    )
"""
import io, os, subprocess, tempfile, textwrap, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
NAME = "Chivato Ofertas"   # nombre visible en X
HANDLE = "@AlexExplorer_"   # cámbialo aquí si cambias la @

FONT_DIR = "/usr/share/fonts/opentype/inter"
F_BLACK = os.path.join(FONT_DIR, "Inter-Black.otf")
F_BOLD = os.path.join(FONT_DIR, "Inter-Bold.otf")
F_MED = os.path.join(FONT_DIR, "Inter-Medium.otf")

BG = (10, 10, 12)
ORANGE = (255, 153, 0)
WHITE = (245, 245, 245)
GREY = (150, 150, 150)
RED = (230, 45, 60)


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:  # en el VPS puede no estar Inter
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)


def _eur(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + "€"


def _load_image(src):
    if src.startswith("http"):
        import requests
        r = requests.get(src, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    return Image.open(src).convert("RGB")


def _center(d, y, text, font, fill):
    b = d.textbbox((0, 0), text, font=font)
    d.text(((W - (b[2] - b[0])) // 2 - b[0], y - b[1]), text, font=font, fill=fill)
    return y + (b[3] - b[1])


def _bars(d):
    d.rectangle([0, 0, W, 14], fill=ORANGE)
    d.rectangle([0, H - 14, W, H], fill=ORANGE)


def _pill(d, cy, text, font, bg, fg):
    b = d.textbbox((0, 0), text, font=font)
    tw, th = b[2] - b[0], b[3] - b[1]
    px, py = 40, 22
    x0 = (W - tw) // 2 - px
    d.rounded_rectangle([x0, cy - th // 2 - py, x0 + tw + 2 * px, cy + th // 2 + py],
                        radius=(th + 2 * py) // 2, fill=bg)
    d.text((x0 + px - b[0], cy - th // 2 - b[1]), text, font=font, fill=fg)


# ---------- escenas ----------
def _scene_hook(pct, badge):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    _bars(d)
    _pill(d, 640, badge or "CHOLLAZO", _font(F_BLACK, 64), ORANGE, BG)
    size = 340
    while d.textlength(f"-{pct}%", font=_font(F_BLACK, size)) > W - 160:
        size -= 10
    _center(d, 790, f"-{pct}%", _font(F_BLACK, size), ORANGE)
    _center(d, 1260, "¿Lo vas a dejar escapar?", _font(F_MED, 62), WHITE)
    return im


def _scene_product(title, prod, price, old_price, pct):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    _bars(d)
    # tarjeta blanca con la foto
    cx0, cy0, cx1, cy1 = 90, 170, W - 90, 1070
    d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=48, fill=(255, 255, 255))
    p = prod.copy()
    p.thumbnail((cx1 - cx0 - 120, cy1 - cy0 - 120), Image.LANCZOS)
    im.paste(p, ((W - p.width) // 2, cy0 + (cy1 - cy0 - p.height) // 2))
    # sello de descuento
    f = _font(F_BLACK, 70)
    txt = f"-{pct}%"
    b = d.textbbox((0, 0), txt, font=f)
    bx, by = cx1 - (b[2] - b[0]) - 80, cy0 - 40
    d.rounded_rectangle([bx, by, bx + (b[2] - b[0]) + 60, by + (b[3] - b[1]) + 50], radius=30, fill=RED)
    d.text((bx + 30 - b[0], by + 25 - b[1]), txt, font=f, fill=WHITE)
    # título (máx. 3 líneas)
    ft = _font(F_BOLD, 54)
    lines = textwrap.wrap(title, 30)[:3]
    if len(textwrap.wrap(title, 30)) > 3:
        lines[-1] = lines[-1].rstrip(" ,.-") + "…"
    y = 1130
    for ln in lines:
        y = _center(d, y, ln, ft, WHITE) + 22
    # precios
    y += 40
    fo = _font(F_MED, 70)
    old = _eur(old_price)
    b = d.textbbox((0, 0), old, font=fo)
    ox = (W - (b[2] - b[0])) // 2
    d.text((ox - b[0], y - b[1]), old, font=fo, fill=GREY)
    mid = y + (b[3] - b[1]) // 2
    d.line([ox - 10, mid, ox + (b[2] - b[0]) + 10, mid], fill=GREY, width=7)
    _center(d, y + (b[3] - b[1]) + 40, _eur(price), _font(F_BLACK, 190), ORANGE)
    return im


def _scene_cta():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    _bars(d)
    y = _center(d, 620, "Enlace en el post", _font(F_BLACK, 100), WHITE)
    # flecha hacia abajo
    ax, ay = W // 2, y + 70
    d.rectangle([ax - 14, ay, ax + 14, ay + 120], fill=ORANGE)
    d.polygon([(ax - 70, ay + 110), (ax + 70, ay + 110), (ax, ay + 200)], fill=ORANGE)
    y = _center(d, ay + 280, "Sígueme para más chollos", _font(F_MED, 62), GREY)
    y = _center(d, y + 50, NAME, _font(F_BLACK, 100), WHITE)
    _center(d, y + 30, HANDLE, _font(F_BOLD, 70), ORANGE)
    return im


# ---------- música (original, generada) ----------
def _music(path, dur, bpm=124, sr=44100):
    t = np.arange(int(sr * dur)) / sr
    beat = 60 / bpm
    out = np.zeros_like(t)
    # bombo en cada tiempo
    for k in np.arange(0, dur, beat):
        i = int(k * sr); n = min(int(0.25 * sr), len(t) - i)
        tt = np.arange(n) / sr
        out[i:i + n] += 0.9 * np.sin(2 * np.pi * (50 + 90 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 9)
    # hi-hat en contratiempo
    rng = np.random.default_rng(1)
    for k in np.arange(beat / 2, dur, beat):
        i = int(k * sr); n = min(int(0.05 * sr), len(t) - i)
        out[i:i + n] += 0.18 * rng.standard_normal(n) * np.exp(-np.arange(n) / sr * 80)
    # bajo/acorde por compases: La m - Fa - Do - Sol
    roots = [110.0, 87.31, 130.81, 98.0]
    bar = beat * 4
    for j, k in enumerate(np.arange(0, dur, bar)):
        i = int(k * sr); n = min(int(bar * sr), len(t) - i)
        tt = np.arange(n) / sr
        f = roots[j % 4]
        env = np.minimum(1, tt * 20) * np.exp(-tt * 0.6)
        out[i:i + n] += 0.22 * env * (np.sign(np.sin(2 * np.pi * f * tt)) * 0.4 + np.sin(2 * np.pi * f * 2 * tt))
        out[i:i + n] += 0.08 * env * (np.sin(2 * np.pi * f * 3 * tt) + np.sin(2 * np.pi * f * 2.52 * tt))
    fade = int(0.6 * sr)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = out / (np.abs(out).max() + 1e-9) * 0.8
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def _run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def _encode_still(png, dur, out, fade=0.25):
    tmp = out + ".part.mp4"
    vf = (f"format=yuv420p,loop=-1:1,trim=duration={dur},setpts=N/{FPS}/TB,"
          f"fade=t=in:st=0:d={fade},fade=t=out:st={dur - fade}:d={fade}")
    _run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", png, "-vf", vf, "-r", str(FPS),
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", tmp])
    os.replace(tmp, out)


def make_offer_video(title, image, price, old_price, out, badge=None, durations=(2.2, 4.8, 2.5)):
    pct = round((1 - price / old_price) * 100)
    prod = _load_image(image)
    with tempfile.TemporaryDirectory() as td:
        scenes = [_scene_hook(pct, badge), _scene_product(title, prod, price, old_price, pct), _scene_cta()]
        parts = []
        for i, (im, dur) in enumerate(zip(scenes, durations)):
            png, mp4 = os.path.join(td, f"s{i}.png"), os.path.join(td, f"s{i}.mp4")
            im.save(png)
            _encode_still(png, dur, mp4)
            parts.append(mp4)
        lst = os.path.join(td, "list.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{p}'\n" for p in parts)
        silent = os.path.join(td, "v.mp4")
        _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
        wav = os.path.join(td, "m.wav")
        _music(wav, sum(durations))
        tmp = out + ".part.mp4"
        _run(["ffmpeg", "-y", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", tmp])
        os.replace(tmp, out)
    return out


def send_to_telegram(video_path, caption, token, chat_id):
    """Manda el vídeo al admin por Telegram para subirlo a X desde el móvil."""
    import requests
    with open(video_path, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendVideo",
                          data={"chat_id": chat_id, "caption": caption[:1024], "supports_streaming": True},
                          files={"video": f}, timeout=120)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    make_offer_video(
        title="Nintendo Switch 2 Cámara HD con Micrófono Integrado y Conexión USB-C",
        image="prod_test.png", price=20.90, old_price=59.99,
        out="demo_oferta.mp4", badge="MÍNIMO HISTÓRICO",
    )
    print("ok")
