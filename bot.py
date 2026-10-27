import os, re, json, requests
import xml.etree.ElementTree as ET

TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT"]
TAG = "alexexplore0e-21"
MIN_DESC = 0
SOLO_AMAZON = True
RSS = "https://www.chollometro.com/rss"
SEEN = "seen.json"

try:
    seen = json.load(open(SEEN))
except Exception:
    seen = {}

def num(s):
    s = s.strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.search(r"\.\d{2}$", s):
        pass
    else:
        s = s.replace(".", "")
    return float(s)

def descuento(txt):
    best = 0
    for m in re.findall(r"(\d{2,3})\s*%", txt):
        best = max(best, int(m))
    precios = []
    for m in re.findall(r"(\d[\d.]*(?:,\d{1,2})?)\s*€", txt):
        try:
            p = num(m)
            if p > 0:
                precios.append(p)
        except Exception:
            pass
    if len(precios) >= 2:
        best = max(best, round((1 - min(precios) / max(precios)) * 100))
    return best

def asin_de(txt):
    m = re.search(r"amazon\.es/(?:[^\s\"'<>]*?/)?(?:dp|gp/product)/([A-Z0-9]{10})", txt)
    return m.group(1) if m else None

r = requests.get(
    RSS,
    headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"},
    timeout=60,
)
print("HTTP", r.status_code, len(r.text))
root = ET.fromstring(r.content)
con_afiliado = 0
total = 0

for it in root.iter("item"):
    try:
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        raw = it.findtext("description") or ""
        desc = re.sub(r"<[^>]+>", " ", raw)
        merchant = " ".join(
            " ".join(e.attrib.values()) + " " + (e.text or "")
            for e in it if e.tag.lower().endswith("merchant")
        )
        blob = f"{title} {desc} {merchant}".lower()
        if SOLO_AMAZON and "amazon" not in blob:
            continue
        d = descuento(title)
        if d < MIN_DESC or link in seen:
            continue
        asin = asin_de(raw + " " + merchant)
        total += 1
        if asin:
            url = f"https://www.amazon.es/dp/{asin}?tag={TAG}"
            con_afiliado += 1
        else:
            url = link
        msg = f"🔥 ~-{d}%\n{title}\n{url}\n\n(Enlace de afiliado: gano una comisión sin coste para ti)"
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT, "text": msg},
            timeout=30,
        )
        seen[link] = 1
    except Exception as e:
        print("error", e)

print("avisos:", total, "con tu afiliado:", con_afiliado)
json.dump(dict(list(seen.items())[-2000:]), open(SEEN, "w"))
