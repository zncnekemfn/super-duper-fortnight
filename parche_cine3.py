import re, sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- CINE3 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- CINE1 ---" not in src:
    print("ABORTO: falta el parche cine2 (CINE1)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: anclaje final (%d)" % len(anc)); sys.exit(1)
nombres = []
for m in re.finditer(r'(?m)^def (_vd\w*render\w*)\(', src):
    if m.group(1) not in nombres and m.group(1) != "_vd_render":
        nombres.append(m.group(1))
print("Dibujantes de video encontrados:", ", ".join(nombres) or "(ninguno extra)")
BLOQUE = r'''# --- CINE3 ---
import inspect as _c3_insp
_C3_NOMBRES = %s

def _c3_video(foto, titulo, ahora, antes, pct, ruta):
    global VD_W, VD_H
    try:
        _vd11_estado["neon"] = False
    except Exception:
        pass
    VD_W, VD_H = 720, 720
    dat = {"titulo": titulo, "ahora": float(ahora), "antes": float(antes), "pct": int(pct), "foto": foto}
    try:
        mr = _ft_re.search(r"([\d.,]+)\s*·\s*([\d.]+)\s*valoraci", _vn_valoracion(getattr(_cn_loc, "asin", None)) or "")
        if mr:
            dat["rat"] = mr.group(1); dat["nv"] = mr.group(2)
    except Exception:
        pass
    total, fps = 6.0, 30
    tmp = ruta + ".tmp.mp4"
    p = _cn_sp.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1080",
                      "-r", str(fps), "-i", "-", "-vf", "scale=720:720", "-c:v", "libx264",
                      "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-f", "mp4", tmp],
                     stdin=_cn_sp.PIPE)
    for i in range(int(total * fps)):
        p.stdin.write(_cn_frame(dat, i / float(fps), total, False).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg fallo")
    _cn_os.replace(tmp, ruta)

def _c3_envolver(nombre):
    orig = globals().get(nombre)
    if orig is None or getattr(orig, "_c3", False):
        return
    def nuevo(*a, **k):
        try:
            ba = _c3_insp.signature(orig).bind(*a, **k)
            ba.apply_defaults()
            P = ba.arguments
            for x in ("titulo", "ahora", "antes", "pct", "ruta"):
                if x not in P:
                    raise TypeError("firma distinta")
            foto = None
            im = P.get("imagen")
            if im is not None:
                try:
                    foto = im.convert("RGB")
                except Exception:
                    from PIL import Image
                    foto = Image.open(_cn_io.BytesIO(im)).convert("RGB")
            if foto is None:
                try:
                    foto = _cn_foto(getattr(_cn_loc, "asin", None))
                except Exception:
                    foto = None
            _c3_video(foto, P["titulo"], P["ahora"], P["antes"], P["pct"], P["ruta"])
            return
        except Exception as e:
            print("error video cine3", nombre, e, flush=True)
        return orig(*a, **k)
    nuevo._c3 = True
    globals()[nombre] = nuevo

for _n in _C3_NOMBRES + ["_vd_render"]:
    _c3_envolver(_n)
''' % repr(nombres)
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_cine3_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Listo. Copia:", cp)
print("Ahora ejecuta: systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& systemctl restart chivato")
