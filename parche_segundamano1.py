import re, sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- SEGUNDAMANO ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def ejecutar(", "def comando(", "def enviar(", "def guardar(", "_foto = [None]"):
    if n not in src:
        print("ABORTO: no encuentro %s" % n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: anclaje final (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''# --- SEGUNDAMANO ---
import re as _sm_re

def _sm_dat(d):
    s = d.setdefault("segunda", {"n": 0, "items": {}})
    s.setdefault("n", 0); s.setdefault("items", {})
    return s

def _sm_hace(ts):
    m = int((time.time() - ts) / 60)
    if m < 1: return "hace un momento"
    if m < 60: return "hace %d min" % m
    return "hace %d h" % (m // 60)

def _sm_limpio(s, n):
    s = _sm_re.sub(r"[<>&]", " ", str(s or ""))
    return _sm_re.sub(r"\s+", " ", s).strip()[:n]

def _sm_texto(it, extra=""):
    l = ["\U0001f6cd️ " + it["t"]]
    if it.get("p"):
        l.append("\U0001f4b6 " + it["p"])
    if it.get("d"):
        l.append(it["d"])
    l.append("\U0001f552 " + _sm_hace(it.get("ok") or it["ts"]))
    return "\n".join(l) + extra

def _sm_enviar_item(cid, it, boton=True, extra=""):
    txt = _sm_texto(it, extra)
    kb = None
    if boton:
        kb = json.dumps({"inline_keyboard": [[{"text": "\U0001f4ac Contactar", "url": "tg://user?id=%d" % it["u"]}]]})
    if it.get("f"):
        datos = {"chat_id": cid, "photo": it["f"], "caption": txt[:1000]}
        if kb: datos["reply_markup"] = kb
        r = requests.post(API + "/sendPhoto", data=datos, timeout=30)
        if r.status_code == 200:
            return
    if kb: enviar(cid, txt, kb)
    else: enviar(cid, txt)

AYUDA_SM = ("\U0001f6cd️ SEGUNDA MANO\n\n"
            "Para anunciar algo:\n"
            "/vender título | precio | descripción\n"
            "Ejemplo: /vender Nintendo Switch | 150 € | Poco uso, con caja\n\n"
            "Puedes añadir una foto: mándala y escribe el comando en el pie de la foto.\n"
            "Límite: 2 anuncios al día. No se permiten enlaces.\n"
            "Cada anuncio lo revisa el creador antes de publicarse.\n\n"
            "Para ver los de hoy: /segundamano\n"
            "Para quitar uno tuyo: /quitar_N (el número sale en tu anuncio)\n\n"
            "⚠️ Los anuncios son de usuarios. El bot no interviene en la venta: no pagues por adelantado a desconocidos.")

def _sm_manejar(d, cid, texto):
    t = (texto or "").strip()
    if not t.startswith("/"):
        return False
    p = t.split(None, 1)
    cmd = p[0].split("@")[0].lower()
    arg = p[1].strip() if len(p) > 1 else ""
    s = _sm_dat(d)
    ahora = time.time()
    m = _sm_re.match(r"^/(aprobar|rechazar|quitar)_(\d+)$", cmd)
    if m:
        acc, k = m.group(1), m.group(2)
        it = s["items"].get(k)
        if not it:
            enviar(cid, "No encuentro ese anuncio.")
        elif acc == "quitar" and cid != ADMIN and cid != it["u"]:
            enviar(cid, "Ese anuncio no es tuyo.")
        elif acc != "quitar" and cid != ADMIN:
            return False
        elif acc == "aprobar":
            if it["e"] != "pend":
                enviar(cid, "Ese anuncio ya estaba resuelto (%s)." % it["e"])
            else:
                it["e"] = "ok"; it["ok"] = int(ahora); guardar(d)
                enviar(cid, "✅ Anuncio #%s aprobado." % k)
                try: enviar(it["u"], "✅ Tu anuncio ya está publicado. Se ve hoy en /segundamano")
                except Exception: pass
        else:
            it["e"] = "no"; guardar(d)
            enviar(cid, "❌ Anuncio #%s %s." % (k, "rechazado" if acc == "rechazar" else "quitado"))
            if acc == "rechazar":
                try: enviar(it["u"], "❌ Tu anuncio no ha sido aprobado. Revisa que cumpla las normas y vuelve a probar.")
                except Exception: pass
        return True
    if cmd in ("/segundamano", "/segunda", "/segundamano_hoy"):
        vivos = [i for i in s["items"].values() if i["e"] == "ok" and i.get("ok", 0) > ahora - 86400]
        vivos.sort(key=lambda i: i["ok"], reverse=True)
        if not vivos:
            enviar(cid, "\U0001f6cd️ SEGUNDA MANO\n\nHoy todavía no hay anuncios.\nSé el primero: /vender título | precio | descripción")
            return True
        enviar(cid, "\U0001f6cd️ SEGUNDA MANO · anuncios de hoy (%d)\n⚠️ Anuncios de usuarios: no pagues por adelantado a desconocidos." % len(vivos))
        for it in vivos[:10]:
            _sm_enviar_item(cid, it, True, "\n\n/quitar_%d" % it["id"] if cid in (ADMIN, it["u"]) else "")
        if len(vivos) > 10:
            enviar(cid, "Y %d más. Se muestran los 10 más recientes." % (len(vivos) - 10))
        return True
    if cmd in ("/vender", "/anunciar_producto"):
        if not arg or "|" not in arg:
            enviar(cid, AYUDA_SM)
            return True
        partes = [x.strip() for x in arg.split("|")]
        titulo = _sm_limpio(partes[0], 70)
        precio = _sm_limpio(partes[1], 20) if len(partes) > 1 else ""
        desc = _sm_limpio(partes[2], 250) if len(partes) > 2 else ""
        if len(titulo) < 3:
            enviar(cid, "El título es muy corto.\n\n" + AYUDA_SM)
            return True
        if _sm_re.search(r"(?i)https?:|www\.|t\.me|@\w|\.com\b", titulo + " " + precio + " " + desc):
            enviar(cid, "⚠️ Por seguridad no se permiten enlaces ni @usuarios en los anuncios.")
            return True
        recientes = [i for i in s["items"].values() if i["u"] == cid and i["ts"] > ahora - 86400 and i["e"] in ("pend", "ok")]
        if len(recientes) >= 2 and cid != ADMIN:
            enviar(cid, "Has llegado al límite de 2 anuncios al día. Vuelve mañana o quita uno con /quitar_N.")
            return True
        for k in [k for k, i in s["items"].items() if i["ts"] < ahora - 3 * 86400]:
            s["items"].pop(k, None)
        s["n"] += 1
        it = {"id": s["n"], "u": cid, "t": titulo, "p": precio, "d": desc, "f": _foto[0], "ts": int(ahora), "e": "pend"}
        s["items"][str(it["id"])] = it
        guardar(d)
        enviar(cid, "✅ Anuncio enviado a revisión (#%d). Te aviso cuando se publique." % it["id"])
        try:
            _sm_enviar_item(ADMIN, it, False, "\n\n\U0001f194 #%d · de %d\n✅ /aprobar_%d\n❌ /rechazar_%d" % (it["id"], cid, it["id"], it["id"]))
        except Exception as e:
            print("error aviso segundamano", e, flush=True)
        return True
    return False

_ejecutar_pre_sm = ejecutar

def ejecutar(d, cid, texto):
    try:
        if _sm_manejar(d, cid, texto):
            return True
    except Exception as e:
        print("error segundamano", e, flush=True)
    return _ejecutar_pre_sm(d, cid, texto)

_comando_pre_sm = comando

def comando(d, cid, texto):
    try:
        if _sm_manejar(d, cid, texto):
            return True
    except Exception as e:
        print("error segundamano", e, flush=True)
    return _comando_pre_sm(d, cid, texto)

'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_sm_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Segunda mano anadido. Copia:", cp)
print("Ahora ejecuta: systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& systemctl restart chivato")
