# Aparta de la lista de envio a los usuarios que Telegram no encuentra ("chat not found").
# NO los borra: los guarda en data.json -> "inalcanzables" (con todos sus datos) para poder restaurarlos.
# Uso: python3 limpiar_inalcanzables.py           (solo muestra lo que haria)
#      python3 limpiar_inalcanzables.py aplicar   (lo hace: para el bot, edita, lo arranca)
#      python3 limpiar_inalcanzables.py deshacer  (devuelve a esos usuarios a la lista)
import json, os, shutil, subprocess, sys, time
BASE = "/opt/chivato"; DATA = BASE + "/data.json"; LISTA = BASE + "/inalcanzables.txt"
modo = sys.argv[1] if len(sys.argv) > 1 else "ver"
def run(c): subprocess.run(c, shell=True, check=False)
if modo == "deshacer":
    run("sudo systemctl stop chivato")
    d = json.load(open(DATA, encoding="utf-8"))
    ap = d.pop("inalcanzables", {})
    d.setdefault("users", {}).update(ap)
    json.dump(d, open(DATA + ".tmp", "w", encoding="utf-8")); os.replace(DATA + ".tmp", DATA)
    run("sudo systemctl start chivato")
    print("Restaurados %d usuarios." % len(ap)); sys.exit(0)
try:
    ids = [l.strip() for l in open(LISTA) if l.strip()]
except Exception:
    print("Primero ejecuta diag_usuarios_alcanzables.py"); sys.exit(1)
d0 = json.load(open(DATA, encoding="utf-8"))
users0 = d0.get("users", {})
cand = [u for u in ids if u in users0]
print("Usuarios ahora: %d | a apartar (chat not found): %d | quedarian: %d" % (len(users0), len(cand), len(users0) - len(cand)))
if modo != "aplicar":
    print("No he tocado nada. Para hacerlo: python3 limpiar_inalcanzables.py aplicar"); sys.exit(0)
shutil.copy(DATA, DATA + ".bak_limpieza_" + time.strftime("%Y%m%d%H%M%S"))
run("sudo systemctl stop chivato")
d = json.load(open(DATA, encoding="utf-8"))   # releer ya con el bot parado
ap = d.setdefault("inalcanzables", {})
n = 0
for u in ids:
    if u in d.get("users", {}):
        ap[u] = d["users"].pop(u); n += 1
json.dump(d, open(DATA + ".tmp", "w", encoding="utf-8")); os.replace(DATA + ".tmp", DATA)
run("sudo systemctl start chivato")
print("Apartados %d usuarios. Quedan %d. Copia de data.json guardada. Para volver atras: python3 limpiar_inalcanzables.py deshacer" % (n, len(d.get("users", {}))))
