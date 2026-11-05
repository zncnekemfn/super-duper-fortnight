import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- BLACKFRIDAY1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- KEEPACALIDAD2 ---" not in src:
    print("ABORTO: primero hay que tener aplicado parche_keepa_calidad2.py"); sys.exit(1)
for n in ("def _kq2_sel(", "_kp_orig", "def enviar_aviso(", "KEEPA_MAX_POR_CICLO"):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- BLACKFRIDAY1 ---
# Modo Black Friday: del 20-nov-2026 al 1-dic-2026 (ambos incluidos). Fuera de esas fechas no hace nada.
#  - Hasta 10 avisos por ciclo en vez de 5.
#  - Prioridad a los productos que estan en su precio minimo de los ultimos 90 dias (pagina 0 de Keepa).
#    Si Keepa no admite ese filtro, se ignora y solo se aplican el volumen y la etiqueta.
#  - Etiqueta "BLACK FRIDAY" en una linea aparte de los avisos de Amazon.
import datetime as _bf_dt
_BF_INI = _bf_dt.date(2026, 11, 20)
_BF_FIN = _bf_dt.date(2026, 12, 1)
_BF_MAX = 10
_BF_OK = [None]

def _bf_hoy():
    return _bf_dt.date.today()

def _bf_activo():
    return _BF_INI <= _bf_hoy() <= _BF_FIN

_kq2_sel_orig = _kq2_sel

def _bf_probar():
    if _BF_OK[0] is not None:
        return
    try:
        import json as _bf_json
        sel = _kq2_sel_orig(0)
        sel["isLowest90"] = True
        r = requests.get("https://api.keepa.com/deal",
                         params={"key": KEEPA_KEY, "selection": _bf_json.dumps(sel)}, timeout=30)
        if r.status_code == 200 and not r.json().get("error"):
            _BF_OK[0] = True
            print("bf: filtro de minimo de 90 dias activo", flush=True)
        elif r.status_code == 400:
            _BF_OK[0] = False
            print("bf: Keepa no admite isLowest90; solo volumen y etiqueta", flush=True)
    except Exception as e:
        print("bf probar error", str(e)[:100], flush=True)

def _bf_sel(pag):
    if not (_bf_activo() and _BF_OK[0]):
        return _kq2_sel_orig(pag)
    s = _kq2_sel_orig(0)
    if pag == 0:
        s["isLowest90"] = True
    return s

_kq2_sel = _bf_sel
_bf_base = _kp_orig

def _bf_revisar(d):
    global KEEPA_MAX_POR_CICLO
    if not _bf_activo():
        return _bf_base(d)
    _bf_probar()
    viejo = KEEPA_MAX_POR_CICLO
    KEEPA_MAX_POR_CICLO = max(viejo, _BF_MAX)
    try:
        return _bf_base(d)
    finally:
        KEEPA_MAX_POR_CICLO = viejo

_kp_orig = _bf_revisar

_bf_enviar_pre = enviar_aviso

def enviar_aviso(d, cid, item):
    try:
        if _bf_activo() and not item.get("bf") and "amazon.es/dp/" in str(item.get("u") or ""):
            item["bf"] = True
            item["t"] = str(item.get("t") or "") + "\n\U0001f6cd️ BLACK FRIDAY"
    except Exception:
        pass
    return _bf_enviar_pre(d, cid, item)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_blackfriday1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: modo Black Friday (activo solo del 20 nov al 1 dic).")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
