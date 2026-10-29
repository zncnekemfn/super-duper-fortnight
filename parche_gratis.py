import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- TODO GRATIS ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

def opcional(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("AVISO: '%s' encontrado %d veces, no se cambia (no es grave)" % (nombre, n))
        return
    src = re.sub(patron, fn, src, count=1, flags=re.M)

# 1) todos cuentan como apoyantes; la funcion real queda aparte para el spam y las estadisticas
unico(r'^def es_apoyante\(d, cid\):\n',
      lambda m: ('# --- TODO GRATIS ---\n'
                 'def es_apoyante(d, cid):\n    return True\n\n'
                 'def _es_apoyante_real(d, cid):\n'), "es_apoyante")

# 2) el limite de mensajes al creador se mantiene para todos (anti-spam)
unico(r'if not es_apoyante\(d, cid\):(\n\s*c = d\["cuota"\])',
      lambda m: 'if not _es_apoyante_real(d, cid):' + m.group(1), "limite chat")
opcional(r'Los apoyantes \(propina desde \{MIN_PROPINA\} Stars\) tienen chat sin l.mite: /propina',
         lambda m: 'Vuelve ma\\u00f1ana para escribirme otra vez.', "texto limite chat")

# 3) /sinpublicidad deja de existir: todos reciben la publicidad
unico(r'elif cmd == "/sinpublicidad":',
      lambda m: ('elif cmd == "/sinpublicidad":\n'
                 '        enviar(cid, "\\U0001f4e2 La publicidad ayuda a mantener el bot gratis para todos.")\n'
                 '    elif cmd == "/sinpublicidad_off":'), "sinpublicidad")

# 4) texto del plan
opcional(r'^def texto_plan\(d, cid\):\n',
         lambda m: ('def texto_plan(d, cid):\n'
                    '    if _es_apoyante_real(d, cid):\n'
                    '        return "Gratis para todos \\U0001f389 Gracias por tu apoyo \\U0001f49b"\n'
                    '    return "Gratis para todos, sin l\\u00edmites"\n\n'
                    'def _texto_plan_orig(d, cid):\n'), "texto_plan")

# 5) anuncios: el gratis mensual desaparece, todo es de pago (el admin sigue con /anuncio)
unico(r'    ap = es_apoyante\(d, cid\)\n(    sel = d\["ap_sel"\]\.get\(cid\))',
      lambda m: '    ap = False\n' + m.group(1), "ads cmd")
unico(r'    ap = es_apoyante\(d, cid\)\n(    if pk == "free":)',
      lambda m: '    ap = False\n' + m.group(1), "ads cb")
opcional(r'El anuncio gratis es solo para apoyantes\. Mira /propina\.',
         lambda m: 'Los anuncios ahora son solo de pago. Mira /anunciar.', "texto ad gratis")

# 6) textos que hablaban de plan gratis o apoyantes
opcional(r'f"[^"\n]*GRATIS: hasta \{MAX_AVISOS_GRATIS\} avisos al d.a, con \{RETRASO_GRATIS // 60\} min de retraso\.\\n\\n"',
         lambda m: '"\\U0001f193 100 % gratis: todas las ofertas, sin l\\u00edmites.\\n\\n"', "start gratis")
opcional(r'"/propina - [^"\n]*hazte apoyante con una propina\\n"',
         lambda m: '"/propina - \\u2615 apoya el proyecto con una propina (opcional)\\n"', "start propina")
opcional(r'"[^"\n]*/sinpublicidad: quitar la publicidad\\n\\n"',
         lambda m: '"\\n"', "ayuda sinpublicidad")
opcional(r'quieres recibir \(apoyantes\)', lambda m: 'quieres recibir', "ayuda categorias")
opcional(r'\(paquetes de pago; apoyantes: 1 gratis al mes\)', lambda m: '(paquetes de pago)', "ayuda anunciar")

# 7) estadisticas: el contador de apoyantes cuenta solo los de verdad
opcional(r'if es_apoyante\(d, c\):', lambda m: 'if _es_apoyante_real(d, c):', "stats apoyantes")

# 8) al arrancar cada ciclo se limpian los que tenian la publicidad apagada; texto de propina voluntario
unico(r'^if __name__ == ["\']__main__["\']:',
      lambda m: ('TEXTO_PROPINA = ("\\u2615 APOYA EL PROYECTO (opcional)\\n\\n"\n'
                 '    "Todo el bot es gratis para todos. Si te est\\u00e1 siendo \\u00fatil y quieres ayudar a mantenerlo, "\n'
                 '    "puedes dejar una propina en Stars. Es totalmente voluntario, gracias \\U0001f49b")\n\n'
                 '_pu_orig_gratis = procesar_updates\n'
                 'def procesar_updates(d, *a, **k):\n'
                 '    try:\n'
                 '        if d.get("sinpub"):\n'
                 '            d["sinpub"] = {}\n'
                 '    except Exception:\n'
                 '        pass\n'
                 '    return _pu_orig_gratis(d, *a, **k)\n\n') + m.group(0), "main")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_gratis_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
