import re, sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- CARAMELO1 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
a = src.find("# --- CINE1 ---")
if a < 0:
    print("ABORTO: falta el estilo cine (CINE1)"); sys.exit(1)
b = src.find("# --- CINE3 ---")
if b < 0 or b < a:
    b = len(src)
bloque = src[a:b]
CAMBIOS = [
 ("((34, 150), (36, 150), (44, 150))", "((40, 160), (32, 150), (30, 140))"),
 ("(5, 6, 10, 255)", "(6, 5, 4, 255)"),
 ("(9, 11, 17, 255)", "(13, 10, 9, 255)"),
 ("(9, 11, 17, int(", "(13, 10, 9, int("),
 ("(8, 10, 16, 190)", "(14, 10, 8, 190)"),
 ("(8, 10, 16, 200)", "(14, 10, 8, 200)"),
 ("(70, 74, 86)", "(80, 66, 58)"),
 ("(46, 50, 62)", "(62, 50, 44)"),
 ("(120, 255, 214, 230)", "(236, 170, 98, 235)"),
 ("(120, 255, 214, 160)", "(236, 170, 98, 170)"),
 ("(120, 255, 214, 170)", "(236, 170, 98, 180)"),
 ("(130, 255, 220)", "(236, 170, 98)"),
 ("(150, 255, 225)", "(243, 197, 138)"),
 ("(20, 64, 62, 140)", "(60, 40, 20, 160)"),
 ("(20, 70, 60, 140)", "(60, 40, 20, 160)"),
 ("(14, 18, 28, 190)", "(20, 15, 13, 190)"),
]
n = 0
for x, y in CAMBIOS:
    c = bloque.count(x)
    n += c
    bloque = bloque.replace(x, y)
print("Colores cambiados:", n)
if n < 8:
    print("ABORTO: no encuentro los colores esperados (%d)" % n); sys.exit(1)
EXTRA = r'''
# --- CARAMELO1 ---
# Foto del producto: si Keepa no la da, prueba la imagen clasica de Amazon por ASIN
try:
    _cn_foto_pre_car = _cn_foto
    def _cn_foto(asin):
        img = _cn_foto_pre_car(asin)
        if img is not None or not asin:
            return img
        try:
            from PIL import Image
            for u in ("https://m.media-amazon.com/images/P/%s.01._SCLZZZZZZZ_.jpg" % asin,
                      "https://images-na.ssl-images-amazon.com/images/P/%s.01.LZZZZZZZ.jpg" % asin):
                r = requests.get(u, timeout=15)
                if r.status_code == 200 and len(r.content) > 3000:
                    im = Image.open(_cn_io.BytesIO(r.content)).convert("RGB")
                    if im.width >= 150:
                        _cn_fotos[asin] = im
                        print("cine foto por ASIN ok", asin, flush=True)
                        return im
        except Exception as e:
            print("error foto asin", e, flush=True)
        print("cine sin foto", asin, "imgid=", _CN_IMGID.get(asin), flush=True)
        return None
except NameError:
    pass
'''
nuevo = src[:a] + bloque + src[b:]
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', nuevo))
if len(anc) != 1:
    print("ABORTO: anclaje final (%d)" % len(anc)); sys.exit(1)
nuevo = nuevo[:anc[0].start()] + EXTRA + "\n" + nuevo[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_caramelo_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Avisos y videos en caramelo. Copia:", cp)
print("Ahora ejecuta: systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& systemctl restart chivato")
