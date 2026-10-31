import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO9 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEO8 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_video8.py"); sys.exit(1)

TAIL = r'''# --- VIDEO9 ---
# Gato de dibujo propio que camina sobre la grafica (solo en el modo seguro). /video gato on|off
import math as _vd9_math
_vd9_estado = {"on": True}

def _vd9_gato(t, alto=48, cuerpo=(238, 148, 52), oscuro=(196, 110, 30)):
    from PIL import Image, ImageDraw
    S = 4
    w, h = 110 * S, 80 * S
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ph = t * 2 * _vd9_math.pi * 2.2
    rebote = abs(_vd9_math.sin(ph)) * 2.5 * S
    def P(x, y):
        return (x * S, (y * S) - rebote)
    cola = [P(14 - i * 1.2, 38 - i * 2.6 + _vd9_math.sin(ph * .6 + i * .5) * 3) for i in range(0, 9)]
    d.line(cola, fill=oscuro, width=7 * S // 2, joint="curve")
    for x0, fase, col in ((30, 0, oscuro), (38, _vd9_math.pi, cuerpo), (66, _vd9_math.pi, oscuro), (74, 0, cuerpo)):
        a = _vd9_math.sin(ph + fase) * 7
        d.line([P(x0, 52), P(x0 + a, 70)], fill=col, width=7 * S // 2)
        d.ellipse([P(x0 + a - 4, 68)[0], P(x0 + a, 68)[1], P(x0 + a + 5, 74)[0], P(x0 + a, 74)[1]], fill=col)
    d.ellipse([P(22, 30)[0], P(22, 30)[1], P(84, 58)[0], P(84, 58)[1]], fill=cuerpo)
    d.ellipse([P(76, 20)[0], P(76, 20)[1], P(102, 46)[0], P(102, 46)[1]], fill=cuerpo)
    d.polygon([P(79, 26), P(80, 12), P(88, 22)], fill=cuerpo)
    d.polygon([P(92, 22), P(99, 12), P(100, 27)], fill=cuerpo)
    d.polygon([P(81, 24), P(81.5, 17), P(86, 23)], fill=(245, 175, 150))
    d.ellipse([P(88, 29)[0], P(88, 29)[1], P(93, 34)[0], P(93, 34)[1]], fill=(30, 30, 30))
    d.ellipse([P(97, 30)[0], P(97, 30)[1], P(100, 33)[0], P(100, 33)[1]], fill=(60, 40, 30))
    d.line([P(94, 36), P(102, 34)], fill=(255, 255, 255), width=S)
    for x in (40, 52, 64):
        d.line([P(x, 31), P(x + 2, 42)], fill=oscuro, width=2 * S)
    return im.resize((w // S * alto // 58, h // S * alto // 58), Image.LANCZOS)

_vd8_render_base = _vd8_render

def _vd8_render(titulo, ahora, antes, pct, rating, resenas, hist, resumen, ruta):
    if not _vd9_estado["on"] or not hist:
        return _vd8_render_base(titulo, ahora, antes, pct, rating, resenas, hist, resumen, ruta)
    from PIL import Image
    tmp = ruta + ".base.mp4"
    try:
        _vd8_render_base(titulo, ahora, antes, pct, rating, resenas, hist, resumen, tmp)
        W, H = VD7_W, VD7_H
        dec = _vd_sp.Popen(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=_vd_sp.PIPE)
        enc = _vd_sp.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(VD7_FPS),
                            "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "24", "-movflags", "+faststart", ruta],
                           stdin=_vd_sp.PIPE)
        n = 0
        while True:
            b = dec.stdout.read(W * H * 3)
            if len(b) < W * H * 3:
                break
            t = n / float(VD7_FPS)
            im = Image.frombytes("RGB", (W, H), b)
            if t > 3.4:
                pr = min(1.0, (t - 3.4) / 3.0)
                x = int(-110 + 650 * pr)
                s = _vd9_gato(t if pr < 1.0 else 0.0)
                im.paste(s, (x, 404 - s.height + 6), s)
            enc.stdin.write(im.tobytes())
            n += 1
        enc.stdin.close(); enc.wait(timeout=120); dec.wait(timeout=30)
        if enc.returncode != 0 or not _vd_os.path.exists(ruta):
            raise RuntimeError("ffmpeg gato")
    except Exception as e:
        print("error gato, uso el video sin gato", e, flush=True)
        _vd8_render_base(titulo, ahora, antes, pct, rating, resenas, hist, resumen, ruta)
    finally:
        try:
            if _vd_os.path.exists(tmp):
                _vd_os.remove(tmp)
        except Exception:
            pass
    return ruta

_vd_hacer_v8 = _vd_hacer

def _vd_hacer(d, asin, titulo, ahora, antes, pct, url, destino):
    _vd9_estado["on"] = bool(_vd_d(d).get("gato", True))
    return _vd_hacer_v8(d, asin, titulo, ahora, antes, pct, url, destino)

_video_cmd_v8 = video_cmd

def video_cmd(d, cid, args):
    v = _vd_d(d)
    if args and args[0].lower() == "gato":
        if len(args) > 1 and args[1].lower() in ("on", "off"):
            v["gato"] = (args[1].lower() == "on")
        enviar(cid, "\U0001f431 Gato animado en los videos: %s\n\n/video gato on · /video gato off\n(Solo sale en el modo seguro, sin fotos de Amazon, y cuando hay grafica de precios.)" % (
            "ACTIVADO" if v.get("gato", True) else "APAGADO"))
        return
    return _video_cmd_v8(d, cid, args)

'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video9_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
