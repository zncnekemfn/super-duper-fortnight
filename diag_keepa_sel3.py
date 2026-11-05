#!/usr/bin/env python3
# Diagnostico SOLO LECTURA (parte 3): ordena por euros ahorrados, con precio minimo y
# descuento maximo razonable. No envia nada y no toca bot.py.
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

CALIDAD = {"isFilterEnabled": True, "minRating": 40, "hasReviews": True}
BASE = {
    "page": 0,
    "domainId": 9,
    "priceTypes": [0],
    "isRangeEnabled": True,
    "sortType": 2,  # 2 = ordenar por diferencia absoluta (euros ahorrados)
}


def con(**c):
    s = dict(BASE)
    s.update(CALIDAD)
    s.update(c)
    return s


PRUEBAS = [
    (
        "J  90 dias, 25-70%, precio desde 15 EUR, ahorro desde 10 EUR",
        con(dateRange=3, deltaPercentRange=[25, 70], currentRange=[1500, 200000],
            deltaRange=[1000, 200000], salesRankRange=[1, 100000]),
    ),
    (
        "K  mes, 25-70%, precio desde 15 EUR, ahorro desde 10 EUR",
        con(dateRange=2, deltaPercentRange=[25, 70], currentRange=[1500, 200000],
            deltaRange=[1000, 200000], salesRankRange=[1, 100000]),
    ),
    (
        "L  90 dias, 30-70%, precio desde 25 EUR, ahorro desde 15 EUR, ventas top 30.000",
        con(dateRange=3, deltaPercentRange=[30, 70], currentRange=[2500, 200000],
            deltaRange=[1500, 200000], salesRankRange=[1, 30000]),
    ),
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
    for dl in lista[:10]:
        cur = num([dl.get("current") or []], 0, 0)
        m90 = num(dl.get("avg") or [], 3, 0)
        d90 = int(round(100.0 * (m90 - cur) / m90)) if m90 and cur else 0
        ahorro = (m90 - cur) / 100.0 if m90 and cur else 0.0
        print("   %.2f EUR | -%d%% vs 90d | ahorras %.0f EUR | %s" % (
            cur / 100.0, d90, ahorro, (dl.get("title") or dl.get("asin") or "")[:36]))
