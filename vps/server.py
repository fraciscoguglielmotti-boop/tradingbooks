#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor de la invitación + RSVP para el cumple de 60 de Christian.
Solo usa la librería estándar de Python 3 (no hay que instalar nada).

Sirve:
  - la invitación (index.html) y sus archivos (audio/, img/, etc.)
  - POST /rsvp   -> guarda una confirmación en rsvp.jsonl
  - GET  /admin?key=CLAVE      -> panel con todas las confirmaciones
  - GET  /admin.csv?key=CLAVE  -> descarga en CSV

Variables de entorno (opcionales):
  PORT       puerto (por defecto 80)
  WEB_DIR    carpeta con index.html (por defecto, la de este archivo)
  INDEX_FILE nombre del archivo principal (por defecto index.html)
  DATA_FILE  archivo donde se guardan las confirmaciones
  ADMIN_KEY  clave para ver el panel (¡cambiala!)
"""
import json, os, time, csv, io, html, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WEB_DIR   = os.environ.get("WEB_DIR", os.path.dirname(os.path.abspath(__file__)))
INDEX     = os.environ.get("INDEX_FILE", "index.html")
DATA_FILE = os.environ.get("DATA_FILE", os.path.join(WEB_DIR, "rsvp.jsonl"))
ADMIN_KEY = os.environ.get("ADMIN_KEY", "cambia-esta-clave")
PORT      = int(os.environ.get("PORT", "80"))

MIME = {".html":"text/html; charset=utf-8", ".css":"text/css; charset=utf-8",
        ".js":"application/javascript; charset=utf-8", ".mp3":"audio/mpeg",
        ".png":"image/png", ".jpg":"image/jpeg", ".jpeg":"image/jpeg",
        ".webp":"image/webp", ".svg":"image/svg+xml", ".ico":"image/x-icon", ".gif":"image/gif"}

def load():
    out = []
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try: out.append(json.loads(line))
                    except Exception: pass
    except FileNotFoundError:
        pass
    return out

def to_csv(rows):
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["Fecha","Nombre","Asiste","Personas","Restricciones","Aclaracion","Mensaje"])
    for r in rows:
        w.writerow([r.get("ts",""), r.get("nombre",""), r.get("asiste",""), r.get("personas",""),
                    " / ".join(r.get("dieta",[])), r.get("dieta_texto",""), r.get("mensaje","")])
    return buf.getvalue()

def admin_html(rows, key):
    e = html.escape
    def _norm(n): return " ".join(str(n).strip().lower().split())
    # Los totales cuentan UNA sola vez por persona (la última confirmación pisa a las
    # anteriores). Se conservan y muestran TODOS los mensajes en la tabla de abajo.
    latest_idx = {}
    for i, r in enumerate(rows):
        nm = _norm(r.get("nombre",""))
        if nm:
            latest_idx[nm] = i
    unicos = [rows[i] for i in latest_idx.values()]
    si = [r for r in unicos if str(r.get("asiste","")).lower().startswith("s")]
    no = [r for r in unicos if str(r.get("asiste","")).lower().startswith("n")]
    cabezas = sum(int(r.get("personas") or 0) for r in si)
    dups = len(rows) - len(unicos)
    trs = ""
    for i, r in reversed(list(enumerate(rows))):
        nm = _norm(r.get("nombre",""))
        es_dup = bool(nm) and latest_idx.get(nm) != i
        viene = str(r.get("asiste","")).lower().startswith("s")
        color = "#1c7a3f" if viene else "#a12b2b"
        rstyle = " style='opacity:.45'" if es_dup else ""
        tag = " <span style='color:#8aa6bf;font-size:11px'>(repetido · no suma)</span>" if es_dup else ""
        trs += (f"<tr{rstyle}>"
                f"<td>{e(str(r.get('ts','')))}</td>"
                f"<td><b>{e(str(r.get('nombre','')))}</b>{tag}</td>"
                f"<td style='color:{color};font-weight:700'>{e(str(r.get('asiste','')))}</td>"
                f"<td style='text-align:center'>{e(str(r.get('personas','')))}</td>"
                f"<td>{e(' / '.join(r.get('dieta',[])))}{' · ' + e(str(r.get('dieta_texto',''))) if r.get('dieta_texto') else ''}</td>"
                f"<td>{e(str(r.get('mensaje','')))}</td>"
                "</tr>")
    return f"""<!doctype html><html lang=es><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>RSVP · Cumple 60 de Christian</title>
<style>
 body{{font-family:system-ui,sans-serif;background:#0e2338;color:#e9e3d3;margin:0;padding:24px}}
 h1{{font-size:20px;margin:0 0 4px}} .sub{{color:#8aa6bf;margin:0 0 18px;font-size:13px}}
 .cards{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}
 .card{{background:#16324e;border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:14px 18px;min-width:120px}}
 .card .n{{font-size:28px;font-weight:800;color:#a6d8ff}} .card .l{{font-size:12px;color:#8aa6bf;text-transform:uppercase;letter-spacing:.1em}}
 table{{width:100%;border-collapse:collapse;background:#0f2439;border-radius:10px;overflow:hidden;font-size:14px}}
 th,td{{padding:9px 11px;text-align:left;border-bottom:1px solid rgba(255,255,255,.06);vertical-align:top}}
 th{{background:#16324e;color:#a6d8ff;font-size:12px;text-transform:uppercase;letter-spacing:.08em}}
 a.btn{{display:inline-block;margin-bottom:16px;background:#2f4f70;color:#fff;text-decoration:none;padding:9px 16px;border-radius:8px;font-size:14px}}
</style></head><body>
<h1>✈ RSVP · Cumple 60 de Christian</h1>
<p class=sub>Actualizá la página para ver las últimas confirmaciones. Los totales cuentan cada persona una sola vez (si alguien confirmó más de una vez, vale la última). Los mensajes repetidos se conservan abajo, en gris.</p>
<div class=cards>
  <div class=card><div class=n>{len(si)}</div><div class=l>Confirmaron</div></div>
  <div class=card><div class=n>{cabezas}</div><div class=l>Personas (total)</div></div>
  <div class=card><div class=n>{len(no)}</div><div class=l>No pueden</div></div>
  <div class=card><div class=n>{dups}</div><div class=l>Envíos repetidos</div></div>
</div>
<a class=btn href="/admin.csv?key={e(key)}">⬇ Descargar CSV</a>
<table><tr><th>Fecha</th><th>Nombre</th><th>Viene</th><th>Pers.</th><th>Restricciones</th><th>Mensaje</th></tr>
{trs if trs else '<tr><td colspan=6 style="color:#8aa6bf">Todavía no hay confirmaciones.</td></tr>'}
</table></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        if isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, "", "text/plain", {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"})

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/admin", "/admin.csv"):
            q = urllib.parse.parse_qs(u.query)
            if q.get("key", [""])[0] != ADMIN_KEY:
                return self._send(401, "No autorizado. Agregá ?key=TU_CLAVE al final.", "text/plain; charset=utf-8")
            rows = load()
            if u.path == "/admin.csv":
                return self._send(200, to_csv(rows), "text/csv; charset=utf-8",
                                  {"Content-Disposition": "attachment; filename=rsvp-christian60.csv"})
            return self._send(200, admin_html(rows, q.get("key", [""])[0]), "text/html; charset=utf-8")
        # archivos estáticos
        rel = INDEX if u.path in ("/", "") else u.path.lstrip("/")
        base = os.path.abspath(WEB_DIR)
        fp = os.path.normpath(os.path.join(base, rel))
        if not fp.startswith(base):
            return self._send(403, "Forbidden", "text/plain; charset=utf-8")
        if os.path.isdir(fp): fp = os.path.join(fp, INDEX)
        if not os.path.isfile(fp):
            return self._send(404, "No encontrado", "text/plain; charset=utf-8")
        with open(fp, "rb") as f: data = f.read()
        ext = os.path.splitext(fp)[1].lower()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != "/rsvp":
            return self._send(404, json.dumps({"ok": False}))
        try:
            ln = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(ln) if ln > 0 else b"{}"
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return self._send(400, json.dumps({"ok": False, "error": "json"}), extra={"Access-Control-Allow-Origin": "*"})
        try: personas = max(1, min(50, int(data.get("personas", 1))))
        except Exception: personas = 1
        rec = {
            "ts": time.strftime("%Y-%m-%d %H:%M"),
            "nombre": str(data.get("nombre", ""))[:80],
            "asiste": str(data.get("asiste", ""))[:10],
            "personas": personas,
            "dieta": [str(x)[:40] for x in (data.get("dieta") or [])][:10],
            "dieta_texto": str(data.get("dieta_texto", ""))[:200],
            "mensaje": str(data.get("mensaje", ""))[:400],
        }
        try:
            with open(DATA_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            return self._send(500, json.dumps({"ok": False}), extra={"Access-Control-Allow-Origin": "*"})
        return self._send(200, json.dumps({"ok": True}), extra={"Access-Control-Allow-Origin": "*"})

    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"Sirviendo {WEB_DIR} en http://0.0.0.0:{PORT}  (admin: /admin?key=****)")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
