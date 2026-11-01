import sys, time, shutil
RUTA = "/opt/chivato/bot.py"
if len(sys.argv) > 1: RUTA = sys.argv[1]
src = open(RUTA, encoding="utf-8").read()
if "# --- VALORACIONES ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
L = src.split("\n")
ih = [i for i, l in enumerate(L) if 'item["h"] = "\\U0001f4ca "' in l]
if len(ih) != 1:
    print("ABORTO: no encuentro la linea del historico (%d)" % len(ih)); sys.exit(1)
ih = ih[0]
ip = [i for i in range(max(0, ih - 40), ih) if "KEEPA_KEY" in L[i] and '"history": 0}' in L[i]]
if not ip:
    print("ABORTO: no encuentro la peticion a Keepa"); sys.exit(1)
ip = [ip[-1]]
L[ip[0]] = L[ip[0]].replace('"history": 0}', '"history": 0, "rating": 1}')
ind = " " * 8
bloque = [
 ind + "# --- VALORACIONES ---",
 ind + "try:",
 ind + "    _cu = st.get('current') or []",
 ind + "    _rt = _cu[16] if len(_cu) > 16 else -1",
 ind + "    _nv = _cu[17] if len(_cu) > 17 else -1",
 ind + "    if _rt is not None and _rt > 0:",
 ind + "        _lr = '\\U00002b50 ' + ('%.1f' % (_rt / 10.0)).replace('.', ',')",
 ind + "        if _nv is not None and _nv > 0:",
 ind + "            _lr += ' \\u00b7 ' + ('{:,}'.format(int(_nv))).replace(',', '.') + ' valoraciones'",
 ind + "        item['h'] = (item['h'] + '\\n' if item.get('h') else '') + _lr",
 ind + "except Exception as _e:",
 ind + "    print('error valoraciones', _e, flush=True)",
]
L[ih+1:ih+1] = bloque
nuevo = "\n".join(L)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_val_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Valoraciones anadidas. Copia:", cp)
print("Ahora ejecuta: systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& systemctl restart chivato")
