"""
servidor_cotacoes.py
────────────────────
Servidor HTTP local para o Dashboard de Cotações Químicos.

Detecção de mudança — SEM polling por timer:
  1. watchdog  → evento do sistema operacional (inotify/FSEvents/ReadDirectoryChanges)
                 reage em milissegundos quando o OneDrive grava o arquivo
  2. schedule  → força re-leitura nos 3 horários fixos configurados abaixo
                 (redundância para casos onde o evento do SO não dispara)

Consumo em idle: praticamente zero — a thread watchdog dorme bloqueada
esperando evento do kernel, sem loop ativo.

Instalação das dependências (apenas uma vez):
    pip install watchdog schedule

Uso:
    python servidor_cotacoes.py
"""

import hashlib
import http.server
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# ── DEPENDÊNCIAS OPCIONAIS ────────────────────────────────────────────────────
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────
# Altere para o caminho real do arquivo na pasta sincronizada do OneDrive.
# Windows : r"C:\Users\SEU_USUARIO\OneDrive\historico_precos_quimicos.xlsx"
# macOS   : "/Users/seu_usuario/Library/CloudStorage/OneDrive-Personal/historico_precos_quimicos.xlsx"

XLSX_PATH = Path(r"C:\Users\lsilva\OneDrive - Meridional TCS Ind e Com de Oleos S A\Arquivos\Python\importado\historico_precos_quimicos.xlsx")

PORT = 8765  # porta local — mude se já estiver em uso

# Horários fixos de re-leitura garantida (HH:MM, 24h)
SCHEDULED_TIMES = ["09:15", "12:00", "17:00"]

# Fallback: se watchdog e schedule não estiverem instalados, usa este intervalo (segundos)
FALLBACK_POLL_SECS = 300
# ──────────────────────────────────────────────────────────────────────────────

_state_lock   = threading.Lock()
_file_hash    = None
_file_mtime   = None
_last_event   = None
_event_source = None


# ── HASH ──────────────────────────────────────────────────────────────────────

def compute_hash(path):
    try:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def refresh_state(source):
    global _file_hash, _file_mtime, _last_event, _event_source
    new_hash = compute_hash(XLSX_PATH)
    try:
        new_mtime = XLSX_PATH.stat().st_mtime if XLSX_PATH.exists() else None
    except OSError:
        new_mtime = None

    with _state_lock:
        changed       = new_hash != _file_hash
        _file_hash    = new_hash
        _file_mtime   = new_mtime
        _last_event   = datetime.now().isoformat()
        _event_source = source

    if changed and source != "startup":
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] Arquivo alterado — detectado via {source}")


# ── WATCHDOG ──────────────────────────────────────────────────────────────────

if HAS_WATCHDOG:
    class XlsxEventHandler(FileSystemEventHandler):
        def __init__(self, target):
            self.target = Path(target).resolve()

        def _is_target(self, p):
            try:
                return Path(p).resolve() == self.target
            except Exception:
                return False

        def on_modified(self, event):
            if not event.is_directory and self._is_target(event.src_path):
                time.sleep(1.5)
                refresh_state("watchdog")

        def on_moved(self, event):
            if not event.is_directory and self._is_target(event.dest_path):
                time.sleep(1.5)
                refresh_state("watchdog")

        def on_created(self, event):
            if not event.is_directory and self._is_target(event.src_path):
                time.sleep(1.5)
                refresh_state("watchdog")


def start_watchdog():
    if not HAS_WATCHDOG:
        return
    handler  = XlsxEventHandler(XLSX_PATH)
    observer = Observer()
    observer.schedule(handler, str(XLSX_PATH.parent), recursive=False)
    observer.daemon = True
    observer.start()
    print(f"  watchdog ativo — monitorando: {XLSX_PATH.parent}")


# ── SCHEDULE ─────────────────────────────────────────────────────────────────

def start_schedule():
    if not HAS_SCHEDULE:
        return

    for t in SCHEDULED_TIMES:
        schedule.every().day.at(t).do(lambda: refresh_state("schedule"))

    def _run():
        while True:
            schedule.run_pending()
            time.sleep(1)

    threading.Thread(target=_run, daemon=True).start()
    print(f"  schedule ativo — horarios: {', '.join(SCHEDULED_TIMES)}")


# ── FALLBACK ──────────────────────────────────────────────────────────────────

def start_fallback_poll():
    def _run():
        while True:
            time.sleep(FALLBACK_POLL_SECS)
            refresh_state("fallback")
    threading.Thread(target=_run, daemon=True).start()
    print(f"  fallback ativo — polling a cada {FALLBACK_POLL_SECS}s")
    print("  Para modo evento instale:  pip install watchdog schedule")


# ── HTTP SERVER ───────────────────────────────────────────────────────────────

class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        msg = fmt % args
        if "/status" not in msg and "/ping" not in msg:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"  [{ts}] {msg}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")

        if path == "/status":
            with _state_lock:
                payload = json.dumps({
                    "hash":       _file_hash,
                    "mtime":      _file_mtime,
                    "exists":     _file_hash is not None,
                    "last_event": _last_event,
                    "source":     _event_source,
                    "timestamp":  datetime.now().isoformat(),
                    "scheduled":  SCHEDULED_TIMES,
                    "watchdog":   HAS_WATCHDOG,
                }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(payload)

        elif path in ("/dados.xlsx", "/dados"):
            if not XLSX_PATH.exists():
                self.send_error(404, f"Arquivo nao encontrado: {XLSX_PATH}")
                return
            try:
                data = XLSX_PATH.read_bytes()
            except OSError as e:
                self.send_error(500, str(e))
                return
            self.send_response(200)
            self.send_header("Content-Type",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition",
                f'attachment; filename="{XLSX_PATH.name}"')
            self.send_header("Content-Length", str(len(data)))
            self.send_cors()
            self.end_headers()
            self.wfile.write(data)

        elif path == "/ping":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_cors()
            self.end_headers()
            self.wfile.write(b"pong")

        else:
            self.send_error(404)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n  Servidor Cotacoes Quimicos — iniciando\n")

    if not XLSX_PATH.exists():
        print(f"  AVISO: arquivo nao encontrado: {XLSX_PATH}")
        print("  Edite XLSX_PATH no topo do script.\n")
    else:
        print(f"  Arquivo: {XLSX_PATH}")

    refresh_state("startup")

    if HAS_WATCHDOG:
        start_watchdog()
    if HAS_SCHEDULE:
        start_schedule()
    if not HAS_WATCHDOG and not HAS_SCHEDULE:
        start_fallback_poll()

    print(f"""
  Endpoints em http://localhost:{PORT}:
    /dados.xlsx  -> arquivo Excel
    /status      -> JSON hash + fonte do evento
    /ping        -> healthcheck

  Horarios fixos : {', '.join(SCHEDULED_TIMES)}
  Evento de escrita (watchdog): {'sim' if HAS_WATCHDOG else 'nao instalado'}
  Ctrl+C para encerrar.
""")

    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor encerrado.")
        sys.exit(0)


if __name__ == "__main__":
    main()
