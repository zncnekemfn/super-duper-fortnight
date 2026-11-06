# Solo lectura: cuenta cuantos usuarios de data.json NO se pueden alcanzar ("chat not found").
# No envia mensajes ni toca data.json. Uso: python3 diag_usuarios_alcanzables.py
import json, re, sys, time
try:
    import requests
except Exception:
    print("Falta 'requests'"); sys.exit(1)
BASE = "/opt/chivato"
tok = ""
for f in (BASE + "/.env", BASE + "/env", BASE + "/chivato.env"):
    try:
        for l in open(f, encoding="utf-8"):
            m = re.search(r"(\d{6,}:[A-Za-z0-9_-]{30,})", l)
            if m and not l.strip().startswith("#") and "KEEPA" not in l.upper():
                tok = m.group(1); break
    except Exception:
        pass
    if tok: break
if not tok:
    print("No encuentro el token del bot en .env"); sys.exit(1)
d = json.load(open(BASE + "/data.json", encoding="utf-8"))
ids = [u for u in (d.get("users") or {}).keys() if re.fullmatch(r"-?\d+", str(u))]
print("Usuarios en data.json:", len(ids))
res = {"ok": 0, "chat not found": 0, "otros": 0}
malos = []
otros = {}
for i, uid in enumerate(ids):
    try:
        r = requests.get("https://api.telegram.org/bot%s/getChat" % tok, params={"chat_id": uid}, timeout=15)
        j = r.json()
        if j.get("ok"):
            res["ok"] += 1
        else:
            desc = str(j.get("description", ""))
            if "chat not found" in desc:
                res["chat not found"] += 1; malos.append(uid)
            else:
                res["otros"] += 1; otros[desc[:60]] = otros.get(desc[:60], 0) + 1
            if j.get("error_code") == 429:
                time.sleep(int((j.get("parameters") or {}).get("retry_after", 3)))
    except Exception as e:
        res["otros"] += 1; otros[str(e)[:50]] = otros.get(str(e)[:50], 0) + 1
    time.sleep(0.06)
print("\nResultado:")
print("  Alcanzables:                 %d" % res["ok"])
print("  NO alcanzables (chat not found): %d" % res["chat not found"])
print("  Otros errores:               %d" % res["otros"])
for k, v in otros.items():
    print("     %d x %s" % (v, k))
open(BASE + "/inalcanzables.txt", "w").write("\n".join(malos))
print("\nLista guardada en /opt/chivato/inalcanzables.txt (no se ha borrado a nadie).")
