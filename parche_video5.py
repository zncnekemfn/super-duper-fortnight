import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO5 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEO4 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_video4.py"); sys.exit(1)

TAIL = r'''# --- VIDEO5 ---
_video_cmd_v2 = video_cmd

def _vd_num(a):
    try:
        return float(str(a).replace(",", ".").replace("€", ""))
    except Exception:
        return None

def video_cmd(d, cid, args):
    if not args or args[0].lower() in _VD_CLAVES:
        return _video_cmd_v2(d, cid, args)
    asin, nums = "", []
    for a in args:
        if a.lower().startswith("http"):
            asin = asin or _vd_de_enlace(a)
        elif _vd_re.fullmatch(r"[A-Za-z0-9]{10}", a) and not asin and not _vd_num(a):
            asin = a.upper()
        elif _vd_num(a) is not None:
            nums.append(_vd_num(a))
    if not asin:
        enviar(cid, "No he podido sacar el ASIN. Envia el enlace de Amazon completo (o corto) o el ASIN.\n"
                    "Ejemplo: /video https://www.amazon.es/dp/B0ABCDEFGH\nCon precios: /video ENLACE 10.29 18.00 (ahora y antes)")
        return
    f = _vd_faltan()
    if f:
        enviar(cid, "Falta instalar: " + " ".join(f) + "\nEjecuta: apt install -y " + " ".join(f)); return
    p = _vd_keepa(d, asin)
    if not p:
        enviar(cid, "Keepa no ha devuelto ese producto."); return
    st = p.get("stats") or {}
    cur, av = st.get("current") or [], st.get("avg90") or []
    def g(l, i):
        return l[i] if len(l) > i and isinstance(l[i], (int, float)) and l[i] > 0 else None
    origen = ""
    if len(nums) >= 2 and nums[1] > nums[0] > 0:
        ahora, antes, origen = nums[0], nums[1], "precios indicados por ti"
    else:
        a_c = g(cur, 18) or g(cur, 0) or g(cur, 1) or g(cur, 10)
        if not a_c:
            enviar(cid, "No encuentro el precio actual de ese producto."); return
        ahora = a_c / 100.0
        lista = g(cur, 4)
        media = max([x for x in (g(av, 0), g(av, 1), g(av, 18)) if x] or [0])
        if len(nums) == 1 and nums[0] > ahora:
            antes, origen = nums[0], "precio anterior indicado por ti"
        elif lista and lista > a_c:
            antes, origen = lista / 100.0, "precio tachado de Amazon"
        elif media and media > a_c:
            antes, origen = media / 100.0, "media de los ultimos 90 dias"
        else:
            enviar(cid, "No hay un precio anterior mayor. Si lo ves tachado en Amazon, escribelo tu:\n/video ENLACE %.2f PRECIO_ANTES" % ahora)
            return
    pct = int(round(100.0 * (antes - ahora) / antes))
    enviar(cid, "Preparando el video de %s: %.2f € (antes %.2f €, -%d%%). Origen del precio anterior: %s." % (asin, ahora, antes, pct, origen))
    _vd_th.Thread(target=_vd_hacer, args=(d, asin, p.get("title") or asin, ahora, antes, pct, "https://www.amazon.es/dp/" + asin, cid), daemon=True).start()

'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video5_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
