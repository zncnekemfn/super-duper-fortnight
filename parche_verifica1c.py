import sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VERIFICA1 ---" not in src:
    print("ABORTO: falta VERIFICA1"); sys.exit(1)
if "# --- VERIFICA1C ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
a = '                cid = m["chat"]["id"]; uid = (m.get("from") or {}).get("id", cid)\n'
if src.count(a) != 1:
    print("ABORTO: no encuentro el punto exacto (%d)" % src.count(a)); sys.exit(1)
b = a + ('                # --- VERIFICA1C --- sin enlace: solo ayuda y NO gasta el tiempo de espera\n'
         '                if len(t.split()) == 1 and not _vf_asin(t):\n'
         '                    enviar(cid, "Pégame un enlace de Amazon.es y te digo si el precio es real.\\nEjemplo: /verifica https://www.amazon.es/dp/B0XXXXXXXX"); return True\n')
nuevo = src.replace(a, b)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_verifica1c_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Corregido: /verifica sin enlace ya no bloquea la siguiente consulta. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
