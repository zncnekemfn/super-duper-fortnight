import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- CANAL1 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if not re.search(r"^def _canal_post\(", src, re.M):
    print("ABORTO: no encuentro _canal_post en el bot"); sys.exit(1)

TAIL = r'''# --- CANAL1 ---
# El bot sigue publicando en el canal, pero ignora todo lo que llegue de el. /ignorarcanal on|off
_canal_post_pre_c1 = _canal_post

def _canal_post(d, post, *a, **k):
    try:
        if d.get("canal_ignorar", True):
            return True
    except Exception:
        pass
    return _canal_post_pre_c1(d, post, *a, **k)

_comando_pre_c1 = comando

def comando(d, cid, texto):
    p = str(texto or "").split()
    if p and p[0].split("@")[0].lower() == "/ignorarcanal" and str(cid) == str(ADMIN):
        if len(p) > 1 and p[1].lower() in ("on", "off"):
            d["canal_ignorar"] = (p[1].lower() == "on")
        enviar(cid, "\U0001f4e2 Ignorar lo que llega del canal: %s\n(El bot sigue publicando en el canal.)\n\n/ignorarcanal on · /ignorarcanal off" % ("SI" if d.get("canal_ignorar", True) else "NO"))
        return
    return _comando_pre_c1(d, cid, texto)

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_canal1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
