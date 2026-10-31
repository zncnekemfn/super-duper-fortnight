import shutil, sys, time, subprocess

# Parche: /video también para tiendas que no son Amazon (Mibro y otras).
# Uso: python3 parche_video_tiendas.py      y luego: systemctl restart chivato
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"

BLOQUE = r'''
# --- VIDEO TIENDAS ---
# /video también para tiendas que no son Amazon (Mibro, tiendas Awin...).
#   /video ENLACE PRECIO_AHORA PRECIO_ANTES   -> ej.: /video https://tidd.ly/xxxx 89.99 149.99
# Saca foto y nombre de la página; si la tienda publica los precios (Shopify, og:price), también.
import json as _vdt_json
from urllib.parse import urlparse as _vdt_up
_vd_cmd_amazon = video_cmd
_VDT_AMZ = _vd_re.compile(r"(^|\.)(amazon\.[a-z.]+|amzn\.[a-z]+|amzn\.to|a\.co|amzlinks?\.[a-z]+)$", _vd_re.I)

def _vdt_host(url):
    try:
        h = (_vdt_up(url).hostname or "").lower()
    except Exception:
        return ""
    return h[4:] if h.startswith("www.") else h

def _vdt_meta(txt, *props):
    for p in props:
        m = (_vd_re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]*content=["\']([^"\']*)' % _vd_re.escape(p), txt, _vd_re.I)
             or _vd_re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name)=["\']%s["\']' % _vd_re.escape(p), txt, _vd_re.I))
        if m and m.group(1).strip():
            import html as _h
            return _h.unescape(m.group(1).strip())
    return ""

def _vdt_num(s):
    try:
        s = str(s).strip().replace("€", "").replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
        else:
            s = s.replace(",", ".")
        v = float(s)
        return v if v > 0 else None
    except Exception:
        return None

def _vdt_pagina(url):
    """Sigue el enlace (corto, Awin...) hasta la tienda y saca titulo, foto y precios si los hay."""
    r = requests.get(url, timeout=20, allow_redirects=True, headers=_VD_UA)
    final, txt = str(r.url), r.text or ""
    m = _vd_re.search(r"awin1\.com/.*?[?&]ued=([^&\"'\s]+)", final) or _vd_re.search(r"[?&]ued=([^&\"'\s]+)", final)
    if m and "awin" in final:
        from urllib.parse import unquote
        destino = unquote(m.group(1))
        r = requests.get(destino, timeout=20, allow_redirects=True, headers=_VD_UA)
        final, txt = str(r.url), r.text or ""
    info = {"url": final, "host": _vdt_host(final),
            "titulo": _vdt_meta(txt, "og:title", "twitter:title"),
            "foto": _vdt_meta(txt, "og:image:secure_url", "og:image", "twitter:image"),
            "ahora": _vdt_num(_vdt_meta(txt, "og:price:amount", "product:price:amount")), "antes": None}
    if not info["titulo"]:
        t = _vd_re.search(r"<title[^>]*>([^<]+)", txt, _vd_re.I)
        info["titulo"] = t.group(1).strip() if t else ""
    if "/products/" in final:
        try:
            j = requests.get(final.split("?")[0].split("#")[0].rstrip("/") + ".js", timeout=15, headers=_VD_UA).json()
            var = None
            vid = _vd_re.search(r"[?&]variant=(\d+)", final)
            for v in j.get("variants") or []:
                if vid and str(v.get("id")) == vid.group(1):
                    var = v
            var = var or (j.get("variants") or [{}])[0]
            pr, comp = var.get("price") or j.get("price"), var.get("compare_at_price") or j.get("compare_at_price")
            if pr:
                info["ahora"] = pr / 100.0
            if comp and pr and comp > pr:
                info["antes"] = comp / 100.0
            info["titulo"] = info["titulo"] or j.get("title") or ""
            foto = (var.get("featured_image") or {}).get("src") if isinstance(var.get("featured_image"), dict) else None
            foto = foto or j.get("featured_image") or ""
            if foto and not info["foto"]:
                info["foto"] = ("https:" + foto) if foto.startswith("//") else foto
        except Exception as ex:
            print("video tiendas shopify", ex, flush=True)
    if info["foto"].startswith("//"):
        info["foto"] = "https:" + info["foto"]
    return info

def _vdt_hacer(d, info, ahora, antes, pct, enlace, nota, destino):
    ruta = None
    try:
        r = requests.get(info["foto"], timeout=20, headers=_VD_UA)
        if r.status_code != 200 or len(r.content) < 2000:
            enviar(destino, "No he podido bajar la foto del producto (%s)." % r.status_code)
            return
        img = _vd_abrir(r.content)
        titulo = _vd_re.sub(r"\s*[|–-]\s*[^|–-]{0,30}$", "", info["titulo"]).strip() or info["titulo"] or info["host"]
        ruta = _vd_os.path.join(_vd_tmp.gettempdir(), "oferta_%s_%d.mp4" % (_vd_re.sub(r"[^a-z0-9]", "", info["host"])[:20], int(time.time())))
        _vd_render(img, titulo, ahora, antes, pct, ruta)
        cap = "\U0001f525 %s\n\n\U0001f4b6 %.2f € (antes %.2f €) · -%d%%\n\n\U0001f449 %s\n\n#publi" % (titulo[:150], ahora, antes, pct, enlace)
        if not _vd_enviar(destino, ruta, cap):
            enviar(destino, "El vídeo se ha generado pero Telegram no lo ha aceptado.")
        elif nota:
            enviar(destino, nota)
    except Exception as e:
        print("error video tiendas", e, flush=True)
        enviar(destino, "Error generando el vídeo: %s" % str(e)[:150])
    finally:
        try:
            if ruta and _vd_os.path.exists(ruta):
                _vd_os.remove(ruta)
        except Exception:
            pass

def video_cmd(d, cid, args):
    urls = [a for a in (args or []) if a.lower().startswith("http")]
    if not urls or _VDT_AMZ.search(_vdt_host(urls[0])):
        return _vd_cmd_amazon(d, cid, args)
    original = urls[0]
    nums = [n for n in (_vdt_num(a) for a in args if not a.lower().startswith("http")) if n]
    try:
        info = _vdt_pagina(original)
    except Exception as e:
        enviar(cid, "No he podido abrir ese enlace: %s" % str(e)[:120]); return
    if _VDT_AMZ.search(info["host"]):
        return _vd_cmd_amazon(d, cid, args)
    f = _vd_faltan()
    if f:
        enviar(cid, "Falta instalar: " + " ".join(f) + "\nEjecuta: apt install -y " + " ".join(f)); return
    if len(nums) >= 2:
        ahora, antes = nums[0], nums[1]
    elif len(nums) == 1:
        ahora, antes = nums[0], info["antes"] or (info["ahora"] if info["ahora"] and info["ahora"] > nums[0] else None)
    else:
        ahora, antes = info["ahora"], info["antes"]
    if not ahora or not antes or antes <= ahora:
        enviar(cid, "Necesito el precio de ahora y el de antes (mayor). La tienda no los da en su página%s.\n"
                    "Escríbelos tú: /video %s AHORA ANTES\nEjemplo: /video %s 89.99 149.99"
                    % (" (he leído %.2f €)" % info["ahora"] if info["ahora"] else "", original, original))
        return
    if not info["foto"]:
        enviar(cid, "No encuentro la foto del producto en esa página. Prueba con el enlace directo del producto."); return
    nota = ""
    if "awin1.com" in original or "tidd.ly" in original:
        enlace = original
    else:
        t = _aw_buscar(d, info["url"]) if "_aw_buscar" in globals() else None
        if t:
            enlace = awin_enlace(t[1], info["url"])
        else:
            enlace = info["url"]
            nota = "⚠️ %s no está en tus tiendas Awin (/awin), así que el enlace del vídeo NO lleva tu afiliado." % info["host"]
    pct = int(round(100.0 * (antes - ahora) / antes))
    enviar(cid, "Preparando el vídeo: %s\n%.2f € (antes %.2f €, -%d%%)" % ((info["titulo"] or info["host"])[:80], ahora, antes, pct))
    _vd_th.Thread(target=_vdt_hacer, args=(d, info, ahora, antes, pct, enlace, nota, cid), daemon=True).start()

'''

s = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO TIENDAS ---" in s:
    print("Este parche ya estaba aplicado. No cambio nada.")
    sys.exit(0)
marca = 'if __name__ == "__main__":'
pos = s.rfind(marca)
if pos < 0 or "# --- VIDEO5 ---" not in s:
    sys.exit("ERROR: no encuentro el bloque de vídeos o el arranque del bot. No he tocado nada.")
bak = RUTA + ".bak_videotiendas_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(s[:pos] + BLOQUE + "\n" + s[pos:])
r = subprocess.run([sys.executable, "-m", "py_compile", RUTA], capture_output=True, text=True)
if r.returncode != 0:
    shutil.copy2(bak, RUTA)
    sys.exit("ERROR: el bot no compila con el parche, he dejado el original.\n" + r.stderr[-800:])
print("Parche aplicado. Copia de seguridad: " + bak)
print("Ahora ejecuta: systemctl restart chivato")
print("Prueba en el bot: /video TU_ENLACE_DE_MIBRO 89.99 149.99")
