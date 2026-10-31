import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- FOTO4 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- FOTO2 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_foto2.py"); sys.exit(1)
viejo = 'nd["caption"] = dat["text"]'
if src.count(viejo) != 1:
    print("ABORTO: no encuentro el punto donde va el pie de foto"); sys.exit(1)
src = src.replace(viejo, 'nd["caption"] = _ft_pie(dat["text"])')

TAIL = r'''# --- FOTO4 ---
# Pie de foto estilo neon-gaming (marco, emojis y barra de ahorro). Texto plano, sin formato.
def _ft_pie(t):
    try:
        item = _ft_item_de_texto(t)
        if not item:
            return t
        lin = t.split("\n")
        iu = [i for i, l in enumerate(lin) if "amazon.es/dp/" in l][0]
        pre = _ft_precios(item["t"], item["d"])
        m = _ft_re.search(r"antes (\d+[.,]\d\d)", item["t"])
        mm = _ft_re.search(r"^(.*?) - (\d+[.,]\d\d) ?(?:EUR|€)", item["t"])
        if not mm:
            return t
        tit = _ft_re.sub(r"(?i)\bamazon\b", "", mm.group(1)); tit = _ft_re.sub(r"\s+", " ", tit).strip()
        ahora = float(mm.group(2).replace(",", "."))
        antes = float(m.group(1).replace(",", ".")) if m else (pre[1] if pre else None)
        pct = int(item["d"])
        money = lambda v: ("%.2f" % v).replace(".", ",") + " €"
        gancho = "PRECIAZO" if pct >= 60 else ("CHOLLO DETECTADO" if pct >= 35 else "BAJADA DE PRECIO")
        n = max(1, min(10, int(round(pct / 10.0))))
        barra = "▰" * n + "▱" * (10 - n)
        sep = "━" * 16
        tl = None
        for l in lin[1:iu]:
            if _ft_re.search(r"\d+[.,]\d\d ?(?:EUR|€)", l) and "Media" not in l:
                tl = l; break
        extras = [l.strip() for l in lin[1:iu] if l.strip() and l is not tl]
        despues = [l.strip() for l in lin[iu + 1:] if l.strip()]
        o = ["⚡ %s ⚡" % gancho, sep, "\U0001f3ae " + tit[:140],
             "\U0001f4a5 -%d%%  ➜  %s" % (pct, money(ahora))]
        if antes and antes > ahora:
            o.append("%s ahorras %s" % (barra, money(antes - ahora)))
        o.append(sep)
        o += extras
        o.append("\U0001f449 " + lin[iu].strip())
        o += despues
        r = "\n".join(o)
        return r if len(r) <= 1024 else t
    except Exception as e:
        print("error pie foto", e, flush=True)
        return t

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_foto4_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
