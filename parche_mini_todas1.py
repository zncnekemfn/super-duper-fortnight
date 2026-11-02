import re, shutil, time, sys
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- MINITODAS1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _mi_registrar(", "def revisar_keepa(", "MI_MAX = 80"):
    if n not in src:
        print("ABORTO: no encuentro", n); sys.exit(1)

BLOQUE = r'''
# --- MINITODAS1 ---
# La mini-app guarda TODAS las ofertas que detecta Keepa (>=MIN_GUARDAR), no solo las que se envian a algun usuario.
_mt_orig = revisar_keepa

def revisar_keepa(d):
    antes = set(id(x) for x in (d.get("recent") or []))
    r = _mt_orig(d)
    try:
        n = 0
        for it in list(d.get("recent") or []):
            if id(it) in antes or it.get("_mi"):
                continue
            it["_mi"] = True
            _mi_registrar(d, it)
            n += 1
        if n:
            print("mini-app: revisadas %d ofertas nuevas, guardadas: %d" % (n, len((d.get("mini") or {}).get("of") or [])), flush=True)
    except Exception as e:
        print("error mini todas", e, flush=True)
    return r
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = src.replace("MI_MAX = 80", "MI_MAX = 200", 1)
nuevo = nuevo.replace('_mi_d(d)["of"][:40]', '_mi_d(d)["of"][:80]')
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), nuevo, count=1, flags=re.M)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
copia = RUTA + ".bak_minitodas_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia:", copia)
print("Ahora ejecuta: systemctl restart chivato")
