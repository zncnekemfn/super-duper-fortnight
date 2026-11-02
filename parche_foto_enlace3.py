import re, shutil, time, sys
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- FOTOENLACE3 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- FOTOENLACE2 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_foto_enlace2.py"); sys.exit(1)
for n in ("def _vdt_pagina(", "def _vdt_host(", "_VDT_AMZ", "def _vdt_num(", "def _cn_frame(", "def _vd_limpio(", "def _vd_cortar(", "def _vd_token("):
    if n not in src:
        print("ABORTO: no encuentro", n); sys.exit(1)

BLOQUE = r'''
# --- FOTOENLACE3 ---
# /foto con enlaces que NO son de Amazon (AliExpress, etc.): misma lectura de pagina que /video.
_fe3_pre_hook = hook_anuncios_pago

def _fe3_imagen(f):
    from PIL import Image
    import io as _io
    if f is None:
        return None
    if hasattr(f, "convert"):
        return f.convert("RGB")
    if isinstance(f, (bytes, bytearray)):
        return Image.open(_io.BytesIO(bytes(f))).convert("RGB")
    if isinstance(f, str):
        if f.startswith("http"):
            r = requests.get(f, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
            return Image.open(_io.BytesIO(r.content)).convert("RGB")
        return Image.open(f).convert("RGB")
    raise RuntimeError("formato de foto no reconocido: %s" % type(f))

def _fe3_hacer(d, original, args, cid):
    ruta = None
    try:
        nums = [n for n in (_vdt_num(a) for a in args if not a.lower().startswith("http")) if n]
        info = _vdt_pagina(original)
        if _VDT_AMZ.search(info.get("host") or ""):
            return _fe2_cmd(d, cid, args)
        if len(nums) >= 2:
            ahora, antes = nums[0], nums[1]
        elif len(nums) == 1:
            ahora = nums[0]
            antes = info.get("antes") or ((info.get("ahora") if info.get("ahora") and info.get("ahora") > nums[0] else None))
        else:
            ahora, antes = info.get("ahora"), info.get("antes")
        if not ahora or not antes or antes <= ahora:
            enviar(cid, "Necesito el precio de ahora y el de antes (mayor). La tienda no los da en su pagina%s.\n"
                        "Escribelos tu: /foto %s AHORA ANTES\nEjemplo: /foto %s 89.99 149.99"
                        % ((" (he leido %.2f €)" % info["ahora"]) if info.get("ahora") else "", original, original))
            return
        if not info.get("foto"):
            enviar(cid, "No encuentro la foto del producto en esa pagina. Prueba con el enlace directo del producto."); return
        foto = _fe3_imagen(info["foto"])
        pct = int(round(100.0 * (antes - ahora) / antes))
        tit = _vd_limpio(info.get("titulo") or info.get("host") or "Oferta")
        tit = re.sub(r"(?i)\s*[-|–]\s*(ali\s*express|amazon).*$", "", tit).strip() or (info.get("host") or "Oferta")
        tit = _vd_cortar(tit, 48)
        host = str(info.get("host") or "").replace("www.", "")
        dat = {"titulo": tit, "ahora": float(ahora), "antes": float(antes), "pct": pct, "foto": foto,
               "hora": time.strftime("AVISO %H:%M · %d/%m/%Y"), "pie1": "Precio en %s en el momento del aviso." % host}
        ruta = _ft_os.path.join(_ft_tmp.gettempdir(), "foto_enlace_%d.jpg" % int(time.time()))
        _cn_frame(dat, 0.0, 6.0, True).save(ruta, "JPEG", quality=92)
        if "awin1.com" in original or "tidd.ly" in original:
            enlace = original
        else:
            t = _aw_buscar(d, info["url"]) if "_aw_buscar" in globals() else None
            enlace = awin_enlace(t[1], info["url"]) if t else info["url"]
        afil = (enlace != info["url"])
        cap = ("⚡ PRECIAZO ⚡\n\n%s\n\U0001f4a5 -%d%% → %.2f € (antes %.2f €)\n\n\U0001f449 %s\n%s" % (
               tit, pct, ahora, antes, enlace, "(Enlace de afiliado.)" if afil else ""))
        with open(ruta, "rb") as fh:
            r = requests.post("https://api.telegram.org/bot%s/sendPhoto" % _vd_token(),
                              data={"chat_id": cid, "caption": cap[:1000]}, files={"photo": fh}, timeout=60)
        if r.status_code != 200:
            enviar(cid, "La foto se ha generado pero Telegram no la ha aceptado.")
        elif not afil:
            enviar(cid, "⚠️ %s no esta en tus tiendas Awin (/awin), asi que el enlace de la foto NO lleva tu afiliado." % host)
    except Exception as e:
        print("error foto enlace3", e, flush=True)
        try: enviar(cid, "Error generando la foto: %s" % str(e)[:150])
        except Exception: pass
    finally:
        try:
            if ruta and _ft_os.path.exists(ruta): _ft_os.remove(ruta)
        except Exception:
            pass

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and t.lower().split("@")[0].split()[0] == "/foto" and str(m["chat"]["id"]) == str(ADMIN):
            args = t.split()[1:]
            urls = [a for a in args if a.lower().startswith("http")]
            if urls and not _VDT_AMZ.search(_vdt_host(urls[0])):
                enviar(m["chat"]["id"], "Preparando la FOTO desde ese enlace...")
                _vd_th.Thread(target=_fe3_hacer, args=(d, urls[0], args, m["chat"]["id"]), daemon=True).start()
                return True
    except Exception as e:
        print("error /foto3", e, flush=True)
    return _fe3_pre_hook(d, u)
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = src
viejo = '"Como afiliado de Amazon obtengo ingresos por las compras adscritas.", font=_cn_sans(17, False)'
if nuevo.count(viejo) >= 1:
    nuevo = nuevo.replace(viejo, '(dat.get("pie1") or "Como afiliado de Amazon obtengo ingresos por las compras adscritas."), font=_cn_sans(17, False)')
    print("Pie de la tarjeta adaptable: sustituido %d vez/veces" % src.count(viejo))
else:
    print("AVISO: no encuentro el pie de la tarjeta; AliExpress saldra con el pie de Amazon")
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), nuevo, count=1, flags=re.M)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
copia = RUTA + ".bak_fotoenlace3_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia:", copia)
print("Ahora ejecuta: systemctl restart chivato")
