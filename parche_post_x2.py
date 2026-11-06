import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- POSTX2 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- POSTX1 ---" not in src:
    print("ABORTO: aplica antes parche_post_x1.py"); sys.exit(1)
viejo = "        enviar(destino, _vs_texto(x))\n    except Exception as e:\n        print(\"error postx\""
if src.count(viejo) != 1:
    print("ABORTO: no encuentro el punto exacto (%d)" % src.count(viejo)); sys.exit(1)
BLOQUE = r'''
# --- POSTX2 ---
# El texto del /post lo escribe Claude: persuasivo, centrado en por que lo necesitas. Datos (precio, enlace) los pone el codigo, no el modelo.
_PX_MODELO = "claude-sonnet-5-5"

def _px_clave():
    k = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if k: return k
    try:
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        for l in open(ruta, encoding="utf-8"):
            l = l.strip()
            if l.startswith("ANTHROPIC_API_KEY="):
                return l.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""

def _px_texto(x):
    key = _px_clave()
    if not key:
        return None
    def e(n): return ("%.2f" % n).replace(".", ",")
    val = ""
    try:
        f = globals().get("_vn_valoracion")
        if f: val = f(x["asin"]) or ""
    except Exception:
        val = ""
    datos = "Producto: %s\nPrecio ahora: %s EUR\nPrecio de referencia (media 90 dias): %s EUR\nDescuento: %d%%\n%s" % (
        re.sub(r"\s+", " ", x["t"]).strip()[:160], e(x["a"]), e(x["b"]), x["pct"], ("Valoraciones: " + val) if val else "")
    prompt = ("Escribe el texto de un post para X (en espanol de Espana) que anime a comprar este articulo de Amazon en oferta. "
              "Explica con naturalidad por que alguien lo necesita o para que situaciones le resuelve la vida, apoyandote SOLO en lo que se deduce del nombre del producto. "
              "Tono cercano y motivador, sin sonar a anuncio; maximo 2 emojis; puedes usar un gancho breve al principio. "
              "No inventes caracteristicas, materiales, marcas ni cifras que no aparezcan abajo. No digas 'garantizado', 'el mejor' ni 'solo hoy'. "
              "No incluyas precio, enlace, hashtags ni aviso legal: los anade el sistema. "
              "Longitud: maximo 150 caracteres. Responde SOLO con el texto del post.\n\n" + datos)
    r = requests.post("https://api.anthropic.com/v1/messages",
                      headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                      json={"model": _PX_MODELO, "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]}, timeout=45)
    if r.status_code != 200:
        raise RuntimeError("API %s %s" % (r.status_code, r.text[:120]))
    cuerpo = r.json()["content"][0]["text"].strip().strip('"')
    cuerpo = re.sub(r"\s+", " ", cuerpo)
    return ("%s\n\n\U0001f4b6 %s \u20ac (antes %s \u20ac) \u00b7 -%d%%\n\U0001f6d2 %s\n\n"
            "M\u00e1s chollos: t.me/ChivatoOfertas_bot\n(enlace afiliado)"
            % (cuerpo, e(x["a"]), e(x["b"]), x["pct"], _rf_enlace(x["asin"])))

def _px_texto_o_aviso(x):
    try:
        t = _px_texto(x)
        if t: return t
        return "Falta la clave de Claude. A\u00f1ade ANTHROPIC_API_KEY=... a /opt/chivato/.env y reinicia el bot."
    except Exception as ex:
        print("error postx texto", str(ex)[:150], flush=True)
        return "No pude escribir el texto: %s" % str(ex)[:120]
'''
nuevo_llamada = "        enviar(destino, _px_texto_o_aviso(x))\n    except Exception as e:\n        print(\"error postx\""
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
out = src.replace(viejo, nuevo_llamada)
out = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), out, count=1, flags=re.M)
if "import os" not in out.split("# --- POSTX2 ---")[0]:
    out = "import os\n" + out
try: compile(out, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
copia = RUTA + ".bak_postx2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(out)
print("OK. El texto del /post ahora lo escribe Claude (modelo %s)." % "claude-sonnet-5-5")
print("Necesitas la clave: echo 'ANTHROPIC_API_KEY=TU_CLAVE' >> /opt/chivato/.env")
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (copia, RUTA))
