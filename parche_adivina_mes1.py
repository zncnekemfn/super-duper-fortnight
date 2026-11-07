import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ADIVINAMES1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- ADIVINA1 ---", "def _ad_responder(", "def _ad_ranking(", "def hook_anuncios_pago(", "def enviar(", "ADMIN", "def _a_ahora("):
    if n not in src:
        print("ABORTO: falta", n, "(primero hace falta el juego /adivina)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- ADIVINAMES1 ---
# Premio mensual de "Adivina el precio": ranking del mes, premio configurable (/premio TEXTO, solo ADMIN),
# y cierre automatico el dia 1: avisa al ADMIN del ganador (con su @usuario) y anuncia el top 3 a los usuarios.
_ADM_MIN_RONDAS = 15
_ADM_PREMIO_DEF = "un producto sorpresa que envía el administrador"

def _adm_mes(): return _a_ahora().strftime("%Y-%m")

def _adm_premio(d): return _ad_d(d).get("premio") or _ADM_PREMIO_DEF

_adm_resp_orig = _ad_responder
def _ad_responder(d, cid, valor, nombre):
    j = _ad_jug(d, cid, nombre)
    antes = j["pts"]
    _adm_resp_orig(d, cid, valor, nombre)
    try:
        m = _adm_mes()
        j["mp"] = {m: j.get("mp", {}).get(m, 0) + (j["pts"] - antes)}
        j["mr"] = {m: j.get("mr", {}).get(m, 0) + 1}
    except Exception as e:
        print("error adivina mes", str(e)[:80], flush=True)

def _adm_top(d, mes, n=10):
    js = [(c, v) for c, v in _ad_d(d)["j"].items() if v.get("mp", {}).get(mes, 0) > 0]
    js.sort(key=lambda x: -x[1]["mp"][mes])
    return js[:n], js

def _ad_ranking(d, cid):
    s = _ad_semana(); mes = _adm_mes()
    sem = [(c, v) for c, v in _ad_d(d)["j"].items() if v["sem"].get(s, 0) > 0]
    sem.sort(key=lambda x: -x[1]["sem"][s])
    med = ["\U0001f947", "\U0001f948", "\U0001f949"]
    lin = ["\U0001f3c6 RANKING · Adivina el precio", "", "SEMANA"]
    lin += ["%s %s · %d pts" % (med[i] if i < 3 else "%d." % (i + 1), v["nom"] or "Jugador", v["sem"][s]) for i, (c, v) in enumerate(sem[:5])] or ["Todavía nadie."]
    top, todos = _adm_top(d, mes, 5)
    lin += ["", "MES (premio)"]
    lin += ["%s %s · %d pts" % (med[i] if i < 3 else "%d." % (i + 1), v["nom"] or "Jugador", v["mp"][mes]) for i, (c, v) in enumerate(top)] or ["Todavía nadie."]
    pos = next((i + 1 for i, (c, v) in enumerate(todos) if c == str(cid)), None)
    mine = _ad_d(d)["j"].get(str(cid), {})
    rondas = mine.get("mr", {}).get(mes, 0)
    if pos:
        lin += ["", "Tu posición en el mes: %d de %d · %d rondas" % (pos, len(todos), rondas)]
    else:
        lin += ["", "Aún no estás en el ranking del mes: juega con /adivina."]
    lin += ["", "\U0001f381 Premio del mes: %s." % _adm_premio(d),
            "Gana quien más puntos sume en el mes (mínimo %d rondas jugadas). Sin compra necesaria. Se cierra el día 1." % _ADM_MIN_RONDAS]
    enviar(cid, "\n".join(lin))

def _adm_cierre(d):
    g = _ad_d(d); mes = _adm_mes()
    ref = g.get("mes_ref")
    if ref is None:
        g["mes_ref"] = mes; return
    if ref == mes:
        return
    g["mes_ref"] = mes
    top, todos = _adm_top(d, ref, 50)
    elig = [(c, v) for c, v in top if v.get("mr", {}).get(ref, 0) >= _ADM_MIN_RONDAS][:3]
    if not elig:
        enviar(ADMIN, "\U0001f3c6 Cierre de %s: nadie llegó a %d rondas, no hay ganador." % (ref, _ADM_MIN_RONDAS)); return
    med = ["\U0001f947", "\U0001f948", "\U0001f949"]
    g_c, g_v = elig[0]
    usr = g_v.get("usr")
    enviar(ADMIN, "\U0001f3c6 GANADOR de %s: %s (%d pts, %d rondas)\nContacto: %s\nID: %s\nPremio: %s\n\nEscríbele para acordar el envío." % (
        ref, g_v["nom"] or "Jugador", g_v["mp"][ref], g_v["mr"][ref], ("@" + usr) if usr else "sin @usuario (escríbele desde el bot)", g_c, _adm_premio(d)))
    try:
        enviar(g_c, "\U0001f389 ¡Has ganado el premio de %s en Adivina el precio!\nPremio: %s.\nTe contactará el administrador para acordar el envío." % (ref, _adm_premio(d)))
    except Exception:
        pass
    txt = "\U0001f3c6 GANADORES DE %s · Adivina el precio\n\n%s\n\nPremio: %s.\n¡Nuevo mes, nueva carrera! Juega con /adivina" % (
        ref, "\n".join("%s %s · %d pts" % (med[i], v["nom"] or "Jugador", v["mp"][ref]) for i, (c, v) in enumerate(elig)), _adm_premio(d))
    def _adm_difundir(cids, t):
        for c in cids:
            try:
                enviar(c, t)
            except Exception:
                pass
            time.sleep(0.1)
    _vd_th.Thread(target=_adm_difundir, args=(list(d["users"].keys()), txt), daemon=True).start()

_adm_hook_orig = hook_anuncios_pago
def hook_anuncios_pago(d, u):
    try:
        _adm_cierre(d)
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t:
            cid = m["chat"]["id"]
            fr = m.get("from") or {}
            j = _ad_d(d)["j"].get(str(cid))
            if j and fr.get("username"):
                j["usr"] = fr["username"]
            prim = t.split()[0].lower().split("@")[0]
            if prim == "/premio" and str(cid) == str(ADMIN):
                arg = t[len(t.split()[0]):].strip()
                if arg:
                    _ad_d(d)["premio"] = arg[:150]
                    enviar(cid, "Premio del mes guardado: %s" % arg[:150])
                else:
                    enviar(cid, "Premio actual: %s\nCámbialo con /premio TEXTO" % _adm_premio(d))
                return True
            if prim == "/adivina" and (t.split() + [""])[1].lower() == "mes":
                _ad_ranking(d, cid); return True
    except Exception as e:
        print("error hook adivina mes", str(e)[:100], flush=True)
    return _adm_hook_orig(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_adivinames_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Premio mensual aplicado. Reinicia: sudo systemctl restart chivato")
print("Prueba: /premio Tu premio aqui  (solo tu)  y  /adivina ranking")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
