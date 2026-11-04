"""Previsión de BTC a 24 h con Kronos (open source) para SolRadar. Se ejecuta en GitHub Actions."""
import json, os, sys, time, urllib.request
import numpy as np, pandas as pd

SALIDA = os.environ.get("SALIDA", "kronos/btc.json")
LOOKBACK, PRED, MUESTRAS = 400, 24, 8

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "solradar-kronos/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def velas():
    """Velas horarias cerradas de BTC/USD: Kraken y, si falla, Coinbase."""
    try:
        j = get("https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60")
        filas = next(v for k, v in j["result"].items() if k != "last")
        df = pd.DataFrame([[int(f[0]), *map(float, f[1:5]), float(f[6])] for f in filas],
                          columns=["t", "open", "high", "low", "close", "volume"])
        fuente = "Kraken"
    except Exception as e:
        print("Kraken falló:", e, file=sys.stderr)
        filas = []
        fin = int(time.time()) // 3600 * 3600
        for k in range(2):  # Coinbase da 300 velas por llamada
            a, b = fin - (k + 1) * 300 * 3600, fin - k * 300 * 3600
            filas += get(f"https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600&start={a}&end={b}")
        df = pd.DataFrame([[int(f[0]), f[3], f[2], f[1], f[4], f[5]] for f in filas],
                          columns=["t", "open", "high", "low", "close", "volume"])
        fuente = "Coinbase"
    df = df.drop_duplicates("t").sort_values("t")
    df = df[df.t + 3600 <= time.time()]  # solo velas cerradas
    return df.tail(LOOKBACK + 48).reset_index(drop=True), fuente

def prever(df, predictor):
    x = df.tail(LOOKBACK).reset_index(drop=True)
    xt = pd.to_datetime(x.t, unit="s")
    yt = pd.Series(pd.date_range(xt.iloc[-1] + pd.Timedelta(hours=1), periods=PRED, freq="h"))
    caminos = []
    for i in range(MUESTRAS):
        try:
            import torch
            torch.manual_seed(1000 + i)
        except Exception:
            pass
        p = predictor.predict(df=x[["open", "high", "low", "close", "volume"]], x_timestamp=xt, y_timestamp=yt,
                              pred_len=PRED, T=1.0, top_p=0.9, sample_count=1, verbose=False)
        caminos.append(np.asarray(p["close"], dtype=float)[:PRED])
    c = np.vstack(caminos)
    return [int(t.timestamp()) for t in yt], c.mean(0), np.percentile(c, 10, axis=0), np.percentile(c, 90, axis=0)

def main(predictor=None):
    previo = {}
    try:
        previo = json.load(open(SALIDA))
    except Exception:
        pass
    df, fuente = velas()
    if len(df) < LOOKBACK:
        sys.exit(f"Pocas velas ({len(df)})")
    if predictor is None:
        sys.path.insert(0, os.environ.get("KRONOS_DIR", "Kronos"))
        from model import Kronos, KronosTokenizer, KronosPredictor
        tok = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
        mod = Kronos.from_pretrained("NeoQuasar/Kronos-small")
        predictor = KronosPredictor(mod, tok, max_context=512)
    ts, media, bajo, alto = prever(df, predictor)
    ahora, t0 = float(df.close.iloc[-1]), int(df.t.iloc[-1])
    # Historial: cada previsión se evalúa 24 h después con el precio real
    hist = [h for h in previo.get("historial", []) if h.get("t0") != t0][-60:]
    cierre = dict(zip(df.t.astype(int), df.close.astype(float)))
    for h in hist:
        if h.get("real") is None and (h["t0"] + PRED * 3600) in cierre:
            h["real"] = round(cierre[h["t0"] + PRED * 3600], 2)
            h["acierto"] = (h["pred"] > h["p0"]) == (h["real"] > h["p0"])
    hist.append({"t0": t0, "p0": round(ahora, 2), "pred": round(float(media[-1]), 2), "real": None, "acierto": None})
    ev = [h for h in hist if h.get("acierto") is not None][-30:]
    salida = {
        "modelo": "Kronos-small", "fuente": fuente, "generado": int(time.time()), "t0": t0, "precio": round(ahora, 2),
        "pasado": [[int(t), round(float(c), 2)] for t, c in zip(df.t.tail(48), df.close.tail(48))],
        "prevision": [[t, round(float(m), 2), round(float(b), 2), round(float(a), 2)] for t, m, b, a in zip(ts, media, bajo, alto)],
        "cambio_24h": round((float(media[-1]) / ahora - 1) * 100, 2),
        "aciertos": {"evaluadas": len(ev), "acertadas": sum(1 for h in ev if h["acierto"])},
        "historial": hist,
    }
    os.makedirs(os.path.dirname(SALIDA) or ".", exist_ok=True)
    json.dump(salida, open(SALIDA, "w"), separators=(",", ":"))
    print(f"BTC {ahora:.0f} -> {media[-1]:.0f} en 24 h ({salida['cambio_24h']:+.2f}%) · aciertos {salida['aciertos']}")

if __name__ == "__main__":
    main()
