import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- COLA ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)
if "# --- MEJORAS A ---" not in src:
    print("ABORTO: primero hay que aplicar parche_A.py")
    sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

TAIL = r'''# --- COLA ---
import threading
import queue

_COLA = queue.Queue()
_MUERTOS = []
_COLA_HILOS = []

def _cola_worker():
    while True:
        cid, msg, mk = _COLA.get()
        try:
            if enviar(cid, msg, mk) == 403:
                _MUERTOS.append(cid)
        except Exception as e:
            print("error cola", e, flush=True)
        time.sleep(0.15)
        _COLA.task_done()

def _cola_iniciar():
    if _COLA_HILOS:
        return
    for _ in range(4):
        t = threading.Thread(target=_cola_worker, daemon=True)
        t.start()
        _COLA_HILOS.append(t)

def _enviar_aviso_cola(d, cid, item):
    """Los avisos se encolan y salen en segundo plano: el bot sigue atendiendo comandos."""
    _cola_iniciar()
    h = ("\n" + item["h"]) if item.get("h") else ""
    msg = "\U0001f525 ~-%s%%\n%s%s\n%s\n\n(%s)" % (item["d"], item["t"], h, item["u"], AVISO)
    _COLA.put((cid, msg, _a_teclado(item)))

_enviar_aviso_orig = _enviar_aviso_cola

_pu_orig_cola = procesar_updates
def procesar_updates(d, *a, **k):
    try:
        while _MUERTOS:
            d["users"].pop(_MUERTOS.pop(), None)
    except Exception as e:
        print("error cola muertos", e, flush=True)
    return _pu_orig_cola(d, *a, **k)

'''

unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_cola_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
