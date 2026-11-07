"""Simulacion en papel: opera BTC de mentira siguiendo a Kronos.

Cada vez que hay una prevision nueva (cada 6 h):
  - si Kronos espera subida >= UMBRAL en 24 h  -> todo en BTC
  - si espera bajada <= -UMBRAL                -> todo en dolares
  - si esta entre medias                       -> no toca nada
Se cobra COMISION en cada compra/venta (como un exchange real).
Se compara con "aguantar": comprar BTC el primer dia y no hacer nada.
No usa dinero real ni claves de nada.
"""
import json, os, time

PREV = os.environ.get("PREV", "kronos/btc.json")
SALIDA = os.environ.get("PAPER", "kronos/paper.json")
CAPITAL = 10000.0
UMBRAL = float(os.environ.get("UMBRAL", "0.5"))      # % de cambio previsto para actuar
COMISION = float(os.environ.get("COMISION", "0.25")) / 100  # 0,25 % por operacion


def main():
    d = json.load(open(PREV))
    precio, t, cambio = float(d["precio"]), int(d["t0"]), float(d["cambio_24h"])

    if os.path.exists(SALIDA):
        p = json.load(open(SALIDA))
    else:
        p = {"inicio": t, "capital": CAPITAL, "precio_inicio": precio, "usd": CAPITAL, "btc": 0.0,
             "umbral": UMBRAL, "comision": COMISION * 100, "operaciones": [], "curva": [], "ultima": 0}

    if t <= p["ultima"]:
        print("prevision ya usada, nada que hacer")
        return

    accion = "esperar"
    if cambio >= UMBRAL and p["usd"] > 1:
        p["btc"] += p["usd"] * (1 - COMISION) / precio
        p["usd"] = 0.0
        accion = "comprar"
    elif cambio <= -UMBRAL and p["btc"] > 0:
        p["usd"] += p["btc"] * precio * (1 - COMISION)
        p["btc"] = 0.0
        accion = "vender"

    valor = p["usd"] + p["btc"] * precio
    hold = p["capital"] * (1 - COMISION) * precio / p["precio_inicio"]
    p["ultima"] = t
    if accion != "esperar":
        p["operaciones"].append({"t": t, "accion": accion, "precio": precio, "prevision": cambio, "valor": round(valor, 2)})
        p["operaciones"] = p["operaciones"][-100:]
    p["curva"].append([t, round(valor, 2), round(hold, 2)])
    p["curva"] = p["curva"][-400:]

    resumen = {
        "desde": p["inicio"],
        "valor": round(valor, 2),
        "kronos_pct": round((valor / p["capital"] - 1) * 100, 2),
        "aguantar_pct": round((hold / p["capital"] - 1) * 100, 2),
        "operaciones": len(p["operaciones"]),
        "posicion": "BTC" if p["btc"] > 0 else "dólares",
        "ultima_accion": accion,
    }
    p["resumen"] = resumen
    json.dump(p, open(SALIDA, "w"), separators=(",", ":"))

    d["paper"] = resumen  # para que la tarjeta de SolRadar lo lea sin otra descarga
    json.dump(d, open(PREV, "w"), separators=(",", ":"))
    print(f"{time.strftime('%Y-%m-%d %H:%M', time.gmtime(t))} prevision {cambio:+.2f}% -> {accion} · "
          f"Kronos {resumen['kronos_pct']:+.2f}% vs aguantar {resumen['aguantar_pct']:+.2f}%")


if __name__ == "__main__":
    main()
