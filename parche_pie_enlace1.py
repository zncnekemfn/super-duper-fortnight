import re, shutil, time, sys
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- PIEENLACE1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- FOTOENLACE2 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_foto_enlace2.py"); sys.exit(1)
if "def _vd_enviar(" not in src:
    print("ABORTO: no encuentro _vd_enviar"); sys.exit(1)

BLOQUE = r'''
# --- PIEENLACE1 ---
# Pie de foto/video de /foto y /video con el mismo formato que los avisos (PRECIAZO, barra de ahorro, etc.)
def _fe4_money(v):
    return ("%.2f" % float(v)).replace(".", ",") + " €"

def _fe4_cap(titulo, ahora, antes, pct, link, extras=None, nota=""):
    gancho = "PRECIAZO" if pct >= 60 else ("CHOLLO DETECTADO" if pct >= 35 else "BAJADA DE PRECIO")
    n = max(1, min(10, int(round(pct / 10.0))))
    barra = "▰" * n + "▱" * (10 - n)
    sep = "━" * 16
    o = ["⚡ %s ⚡" % gancho, sep, "\U0001f3ae " + str(titulo)[:140],
         "\U0001f4a5 -%d%%  ➜  %s" % (pct, _fe4_money(ahora))]
    if antes and antes > ahora:
        o.append("%s ahorras %s" % (barra, _fe4_money(antes - ahora)))
    o.append(sep)
    o += list(extras or [])
    o.append("\U0001f449 " + str(link))
    if nota:
        o.append(nota)
    r = "\n".join(o)
    return r[:1024]

_fe4_vd_pre = _vd_enviar

def _vd_enviar(cid, ruta, texto):
    # videos de enlaces que NO son de Amazon: dar al pie el mismo formato que los avisos
    try:
        if "⚡" not in texto and "amazon.es/dp/" not in texto:
            mp = re.search(r"(\d+[.,]\d\d) ?€ \(antes (\d+[.,]\d\d) ?€\) · -(\d+)%", texto)
            mu = re.search(r"https?://\S+", texto)
            if mp and mu:
                ahora = float(mp.group(1).replace(",", ".")); antes = float(mp.group(2).replace(",", "."))
                tit = re.sub(r"^[^\w]+", "", texto.split("\n")[0]).strip() or "Oferta"
                resto = [l.strip() for l in texto.split("\n")[1:] if l.strip() and mu.group(0) not in l
                         and not re.search(r"€ \(antes", l)]
                extras = ["\U0001f4ca Precio anterior: %s" % _fe4_money(antes)]
                texto = _fe4_cap(tit, ahora, antes, int(mp.group(3)), mu.group(0), extras, " ".join(resto)[:200])
    except Exception as e:
        print("error pie video", e, flush=True)
    return _fe4_vd_pre(cid, ruta, texto)
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = src
cambios = 0
# /foto Amazon (FOTOENLACE2)
pat2 = re.compile(r'^        cap = \(".{0,12}PRECIAZO.*?link\)\n', re.S | re.M)
rep2 = ('        _ex = ["\\U0001f4ca Precio anterior: %s" % _fe4_money(antes)]\n'
        '        if item.get("rat"): _ex.append("\\u2b50 %s \\u00b7 %s valoraciones" % (item["rat"], item.get("nv", "")))\n'
        '        cap = _fe4_cap(titulo, ahora, antes, pct, link, _ex, "(Como afiliado de Amazon obtengo ingresos por las compras adscritas.)")\n')
nuevo, c2 = pat2.subn(lambda m: rep2, nuevo)
# /foto otras tiendas (FOTOENLACE3)
pat3 = re.compile(r'^        cap = \(".{0,12}PRECIAZO.*?"\(Enlace de afiliado\.\)" if afil else ""\)\)\n', re.S | re.M)
rep3 = ('        cap = _fe4_cap(tit, ahora, antes, pct, enlace, ["\\U0001f4ca Precio anterior: %s" % _fe4_money(antes)], "(Enlace de afiliado.)" if afil else "")\n')
nuevo, c3 = pat3.subn(lambda m: rep3, nuevo)
print("Pie de /foto actualizado: Amazon %d, otras tiendas %d" % (c2, c3))
if c2 + c3 == 0:
    print("ABORTO: no encuentro los pies de /foto"); sys.exit(1)
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), nuevo, count=1, flags=re.M)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
copia = RUTA + ".bak_pieenlace_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia:", copia)
print("Ahora ejecuta: systemctl restart chivato")
