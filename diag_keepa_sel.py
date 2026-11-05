#!/usr/bin/env python3
# Diagnostico SOLO LECTURA: prueba distintas selecciones de Keepa /deal y cuenta
# cuantas ofertas devolverian. No envia nada a nadie y no toca bot.py.
# Gasta unos pocos tokens de Keepa (una peticion por prueba).
import json
import os
import subprocess

import requests


def clave():
    k = os.environ.get("KEEPA_KEY", "")
    if k:
        return k
    try:
        pid = subprocess.check_output(
            ["systemctl", "show", "chivato", "-p", "MainPID", "--value"], text=True
        ).strip()
        if pid and pid != "0":
            with open("/proc/%s/environ" % pid, "rb") as f:
                for par in f.read().split(b"\0"):
                    if par.startswith(b"KEEPA_KEY="):
                        return par.split(b"=", 1)[1].decode()
    except Exception as e:
        print("No pude leer la clave de Keepa:", e)
    return ""


KEY = clave()
if not KEY:
    print("Sin clave de Keepa. Ejecuta el script como root en el servidor del bot.")
    raise SystemExit(1)

BASE = {
    "page": 0,
    "domainId": 9,
    "priceTypes": [0],
    "deltaPercentRange": [30, 100],
    "dateRange": 0,
    "isRangeEnabled": True,
    "sortType": 4,
}


def con(**cambios):
    s = dict(BASE)
    s.update(cambios)
    return s


PRUEBAS = [
    ("A actual (como ahora)", con()),
    ("B + 4 estrellas y con resenas", con(isFilterEnabled=True, minRating=40, hasReviews=True)),
    (
        "C = B + ventas top 100.000",
        con(isFilterEnabled=True, minRating=40, hasReviews=True, salesRankRange=[1, 100000]),
    ),
    (
        "D = C + precio de Amazon y marketplace",
        con(
            isFilterEnabled=True, minRating=40, hasReviews=True,
            salesRankRange=[1, 100000], priceTypes=[0, 1],
        ),
    ),
    (
        "E = C pero ultima semana",
        con(
            isFilterEnabled=True, minRating=40, hasReviews=True,
            salesRankRange=[1, 100000], dateRange=1,
        ),
    ),
    (
        "F = C con descuento desde 20%",
        con(
            isFilterEnabled=True, minRating=40, hasReviews=True,
            salesRankRange=[1, 100000], deltaPercentRange=[20, 100],
        ),
    ),
]


def precio_y_pct(dl):
    cur = dl.get("current") or []
    dp = dl.get("deltaPercent") or []
    for t in (0, 1):
        try:
            c = int(cur[t])
            if c > 0:
                return c / 100.0, abs(int(dp[0][t]))
        except Exception:
            continue
    return 0.0, 0


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
    for dl in lista[:6]:
        p, pct = precio_y_pct(dl)
        print("   -%d%% %.2f EUR  %s" % (pct, p, (dl.get("title") or dl.get("asin") or "")[:46]))
