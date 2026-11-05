#!/usr/bin/env python3
# Diagnostico SOLO LECTURA (parte 2): compara el descuento "de hoy" con el descuento
# frente a la media de 30 y 90 dias. No envia nada y no toca bot.py.
import json
import os

import requests


def clave():
    k = os.environ.get("KEEPA_KEY", "")
    if k:
        return k
    ruta = "/opt/chivato/.env"
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea.startswith("export "):
                    linea = linea[7:].strip()
                if "=" in linea:
                    nombre, valor = linea.split("=", 1)
                    if nombre.strip() == "KEEPA_KEY":
                        return valor.strip().strip('"').strip("'")
    return ""


KEY = clave()
if not KEY:
    print("Sin clave de Keepa. Ejecuta el script como root en el servidor del bot.")
    raise SystemExit(1)

CALIDAD = {"isFilterEnabled": True, "minRating": 40, "hasReviews": True, "salesRankRange": [1, 100000]}
BASE = {"page": 0, "domainId": 9, "priceTypes": [0], "isRangeEnabled": True, "sortType": 4}


def con(**c):
    s = dict(BASE)
    s.update(CALIDAD)
    s.update(c)
    return s


PRUEBAS = [
    ("C  como la prueba anterior (hoy)", con(dateRange=0, deltaPercentRange=[30, 100])),
    ("G  frente a la media del MES, desde 30%", con(dateRange=2, deltaPercentRange=[30, 100])),
    ("H  frente a la media de 90 DIAS, desde 30%", con(dateRange=3, deltaPercentRange=[30, 100])),
    ("I  frente a 90 DIAS, desde 25%, ventas top 50.000",
     con(dateRange=3, deltaPercentRange=[25, 100], salesRankRange=[1, 50000])),
]


def num(lista, i, j):
    try:
        v = int(lista[i][j])
        return v if v > 0 else 0
    except Exception:
        return 0


for nombre, sel in PRUEBAS:
    print("\n== " + nombre)
    try:
        r = requests.get(
            "https://api.keepa.com/deal",
            params={"key": KEY, "selection": json.dumps(sel)},
            timeout=40,
        )
    except Exception as e:
        print("  error de red:", e)
        continue
    if r.status_code != 200:
        print("  HTTP", r.status_code)
        continue
    j = r.json()
    if j.get("error"):
        print("  error de Keepa:", str(j["error"])[:160])
        continue
    lista = (j.get("deals") or {}).get("dr") or []
    print("  ofertas:", len(lista), "| tokens restantes:", j.get("tokensLeft"))
    for dl in lista[:8]:
        cur = num([dl.get("current") or []], 0, 0)
        m30 = num(dl.get("avg") or [], 2, 0)
        m90 = num(dl.get("avg") or [], 3, 0)
        d30 = int(round(100.0 * (m30 - cur) / m30)) if m30 and cur else 0
        d90 = int(round(100.0 * (m90 - cur) / m90)) if m90 and cur else 0
        print("   %.2f EUR | vs mes -%d%% | vs 90d -%d%% | %s" % (
            cur / 100.0, d30, d90, (dl.get("title") or dl.get("asin") or "")[:34]))
