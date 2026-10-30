import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- ERRORES2 ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)
if "# --- ERRORES ---" not in src:
    print("ABORTO: falta parche_errores.py")
    sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

AYUDA = r'''# --- ERRORES2 ---
ERR_MAX_REF = 800      # EUR: referencias mayores se consideran precios basura
ERR_PCT_MAX = 95       # bajadas mayores casi siempre son datos falsos
ERR_COOL_ASIN = 7 * 86400
ERR_COOL_TIT = 86400

def _err_clave_tit(titulo):
    t = re.sub(r"[^a-z]", "", (titulo or "").lower())
    return t[:22] if len(t) >= 12 else ""

def _err_repetido(d, asin, titulo, ahora):
    e = _err_d(d)
    ya = e.setdefault("asins", {})
    tt = e.setdefault("tits", {})
    for k in [k for k, v in ya.items() if ahora - v > ERR_COOL_ASIN]:
        ya.pop(k, None)
    for k in [k for k, v in tt.items() if ahora - v > ERR_COOL_TIT]:
        tt.pop(k, None)
    if asin in ya:
        return True
    tk = _err_clave_tit(titulo)
    return bool(tk and tk in tt)

def _err_marcar(d, asin, titulo, ahora):
    e = _err_d(d)
    e.setdefault("asins", {})[asin] = int(ahora)
    tk = _err_clave_tit(titulo)
    if tk:
        e.setdefault("tits", {})[tk] = int(ahora)

'''

unico(r'^def revisar_errores\(d\):\n', lambda m: AYUDA + m.group(0), "revisar_errores")

# filtro de referencia absurda y bajada falsa
unico(r'^            if avg < e\["min"\] \* 100 or pct < e\["pct"\] or pct > 99:\n                continue\n',
      lambda m: ('            if avg < e["min"] * 100 or pct < e["pct"] or pct > ERR_PCT_MAX or avg > ERR_MAX_REF * 100:\n'
                 '                continue\n'
                 '            if _err_repetido(d, asin, dl.get("title"), ahora):\n'
                 '                continue\n'), "filtro")

# marcar en la pasada inicial
unico(r'^                d\["seen"\]\[k1\] = d\["seen"\]\[k2\] = int\(ahora\)\n                continue\n',
      lambda m: ('                d["seen"][k1] = d["seen"][k2] = int(ahora)\n'
                 '                _err_marcar(d, asin, dl.get("title"), ahora)\n'
                 '                continue\n'), "primera")

# marcar al enviar
unico(r'^            d\["seen"\]\[k1\] = d\["seen"\]\[k2\] = int\(ahora\)\n            title = \(dl\.get\("title"\) or asin\)\.strip\(\)\n',
      lambda m: ('            d["seen"][k1] = d["seen"][k2] = int(ahora)\n'
                 '            _err_marcar(d, asin, dl.get("title"), ahora)\n'
                 '            title = (dl.get("title") or asin).strip()\n'), "enviar")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as ex:
    print("ABORTO: el resultado no compila:", ex); sys.exit(1)

copia = RUTA + ".bak_errores2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
