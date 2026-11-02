# Diagnostico: por que la mini-app recibe menos ofertas que el bot (solo lee, no cambia nada)
import json, re, time, subprocess, glob, os, collections
D = "/opt/chivato"
def sh(c):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=60).stdout
    except Exception as e: return str(e)
d = json.load(open(D + "/data.json", encoding="utf-8"))
now = time.time()
of = (d.get("mini") or {}).get("of") or []
print("== MINI-APP ==")
print("ofertas guardadas:", len(of))
for h, n in ((1, "1 h"), (6, "6 h"), (24, "24 h"), (72, "72 h")):
    print("  en las ultimas %s: %d" % (n, sum(1 for o in of if o.get("ts", 0) >= now - h * 3600)))
if of:
    print("  la mas reciente hace %.0f min: %s (-%s%%)" % ((now - of[0]["ts"]) / 60, of[0]["t"][:40], of[0]["pct"]))
    print("  descuento: min %s, max %s" % (min(o["pct"] for o in of), max(o["pct"] for o in of)))
print("\n== BOT (journal 24 h) ==")
j = sh("journalctl -u chivato --since '-24h' --no-pager -o cat")
nuevos = [int(x) for x in re.findall(r"keepa ok, nuevos: (\d+)", j)]
print("ciclos keepa:", len(nuevos), "| productos nuevos detectados:", sum(nuevos))
print("lineas con error/traceback:", len(re.findall(r"(?i)traceback|error", j)))
print("error miniapp registro:", len(re.findall(r"error miniapp registro", j)))
print("\n== FILTROS DE USUARIOS ==")
us = d.get("users") or {}
um = collections.Counter()
for k, u in us.items():
    um[u.get("umbral", "def")] += 1
print("usuarios:", len(us), "| umbrales:", dict(um))
print("\n== CODIGO ==")
b = open(D + "/bot.py", encoding="utf-8").read()
for n in ("MIN_GUARDAR", "UMBRAL_DEF", "MI_MAX", "KEEPA_MAX_POR_CICLO", "MAX_AVISOS_GRATIS"):
    m = re.search(r"^%s\s*=\s*(.+)$" % n, b, re.M)
    print(n, "=", m.group(1).strip() if m else "no encontrado")
print("definiciones de enviar_aviso:", len(re.findall(r"^def enviar_aviso\(", b, re.M)))
print("llamadas a _mi_registrar:", len(re.findall(r"_mi_registrar\(", b)))
i = b.find("def _mi_registrar(")
print("\n-- _mi_registrar --")
print(b[i:i + 1100] if i >= 0 else "no esta")
