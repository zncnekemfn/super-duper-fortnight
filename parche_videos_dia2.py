import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEOSDIA2 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEOSDIA1 ---" not in src:
    print("ABORTO: falta VIDEOSDIA1"); sys.exit(1)
viejo = '            v["dia"] = hoy\n            _vd_th.Thread(target=_vs_hacer, args=(d, ADMIN), daemon=True).start()'
nuevo = ('            v["dia"] = hoy  # --- VIDEOSDIA2 ---\n'
         '            try:\n                guardar(d)\n            except Exception as _e:\n                print("videosdia no pude guardar", str(_e)[:80], flush=True)\n'
         '            _vd_th.Thread(target=_vs_hacer, args=(d, ADMIN), daemon=True).start()')
if src.count(viejo) != 1:
    print("ABORTO: no encuentro el punto exacto (%d)" % src.count(viejo)); sys.exit(1)
out = src.replace(viejo, nuevo)
try: compile(out, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
bak = RUTA + ".bak_videosdia2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(out)
print("OK. Ahora el aviso diario se guarda en disco ANTES de generar los videos: un reinicio ya no los repite.")
print("Reinicia:  sudo systemctl restart chivato")
print("Rollback: cp", bak, RUTA)
