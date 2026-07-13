"""Studio Daemon v0 — the localhost verb surface (Phase 5 core).

One process owns pipeline verbs and the Resolve lifecycle; anything that can
send HTTP (Stream Deck via Companion, curl, a phone shortcut) can drive the
studio. Verbs SHELL THE SAME CLI TOOLS any agent harness uses — the daemon
adds no second implementation (portability doctrine).

    GET  /status            rig snapshot: Resolve, OBS, latest recording/jobs
    GET  /verbs             the verb table
    POST /verb/<name>       fire a verb; JSON body = its arguments
    GET  /jobs              recent jobs
    GET  /jobs/<id>         one job + tail of its log

Long verbs run as background jobs (one at a time — Resolve is a single
instrument); the POST returns a job id immediately. Logs land in
outputs/daemon/job-<id>.log (never /tmp).
"""
import json
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = str(ROOT / ".venv" / "bin" / "python")
LOG_DIR = ROOT / "outputs" / "daemon"
PORT = 8873

_jobs = {}
_jobs_lock = threading.Lock()
_worker_lock = threading.Lock()          # one Resolve-touching job at a time
_seq = 0


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def newest_recording(folder=Path.home() / "Movies"):
    files = [p for p in folder.glob("*") if p.suffix.lower() in
             (".mp4", ".mov") and p.is_file()]
    return max(files, default=None, key=lambda p: p.stat().st_mtime)


# ── verbs ────────────────────────────────────────────────────────────────────
# Each returns either an argv list (run as background job) or a dict
# (answered inline). `args` is the POST body (already parsed).

_RESOLVE_PROBE = """
import sys, json
sys.path.insert(0, {root!r})
from studio.resolve import connect
proj = connect().GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None
print(json.dumps({{"project": proj.GetName() if proj else None,
                   "timeline": tl.GetName() if tl else None}}))
"""


def v_status(args):
    from . import obs as obsmod
    out = {"time": _now()}
    try:
        out["obs"] = obsmod.status()
    except obsmod.OBSUnavailable as e:
        out["obs"] = {"error": str(e)}
    # Resolve probe runs in a SUBPROCESS with a timeout, serialized with jobs:
    # a long-lived in-process fusionscript client concurrent with job clients
    # wedges Resolve's scripting service (learned 2026-07-13).
    if _worker_lock.acquire(timeout=0.1):
        try:
            res = subprocess.run(
                [PY, "-c", _RESOLVE_PROBE.format(root=str(ROOT))],
                capture_output=True, text=True, timeout=12, cwd=ROOT)
            out["resolve"] = json.loads(res.stdout) if res.returncode == 0 \
                else {"error": res.stderr.strip()[-200:]}
        except subprocess.TimeoutExpired:
            out["resolve"] = {"error": "API probe timeout (wedged or busy)"}
        finally:
            _worker_lock.release()
    else:
        out["resolve"] = {"busy": "a job holds the Resolve lock"}
    latest = newest_recording()
    out["latestRecording"] = str(latest) if latest else None
    with _jobs_lock:
        running = [j["id"] for j in _jobs.values() if j["status"] == "running"]
    out["runningJobs"] = running
    return out


def v_record_start(args):
    from . import obs as obsmod
    obsmod.start_record()
    return {"recording": True}


def v_record_stop(args):
    from . import obs as obsmod
    return {"recording": False, "file": obsmod.stop_record()}


def v_ingest_last(args):
    rec = newest_recording()
    if not rec:
        raise ValueError("no recording found in ~/Movies")
    argv = [PY, str(ROOT / "tools" / "ingest-recording.py"), str(rec)]
    if args.get("name"):
        argv += ["--name", args["name"]]
    return argv


def v_stop_and_ingest(args):
    """The deck's money key: stop OBS recording, ingest it immediately."""
    from . import obs as obsmod
    path = obsmod.stop_record()
    time.sleep(1.5)                      # let OBS finalize the container
    argv = [PY, str(ROOT / "tools" / "ingest-recording.py"), path]
    if args.get("name"):
        argv += ["--name", args["name"]]
    return argv


def v_ingest_screensage(args):
    bundles = sorted((Path.home() / "ScreenSage Projects").glob("*.screensage"),
                     key=lambda p: p.stat().st_mtime)
    if args.get("bundle"):
        target = Path(args["bundle"])
    elif bundles:
        target = bundles[-1]
    else:
        raise ValueError("no .screensage bundles found")
    argv = [PY, str(ROOT / "tools" / "ingest-screensage.py"), str(target)]
    if args.get("name"):
        argv += ["--name", args["name"]]
    return argv


def v_compile(args):
    ws = args.get("workspace")
    if not ws:
        raise ValueError("workspace required")
    ir = ROOT / "outputs" / "projects" / ws / "story.json"
    argv = [PY, str(ROOT / "tools" / "compile-ir.py"), str(ir), "--show"]
    if args.get("render"):
        argv.append("--render")
    return argv


def v_deliver(args):
    ws = args.get("workspace")
    if not ws:
        raise ValueError("workspace required")
    argv = [PY, str(ROOT / "tools" / "deliver.py"), ws]
    if args.get("presets"):
        argv += ["--presets", args["presets"]]
    return argv


def v_restart_resolve(args):
    return [PY, str(ROOT / "scripts" / "restart_resolve.py")]


VERBS = {
    "status": v_status,
    "record-start": v_record_start,
    "record-stop": v_record_stop,
    "ingest-last": v_ingest_last,
    "stop-and-ingest": v_stop_and_ingest,
    "ingest-screensage": v_ingest_screensage,
    "compile": v_compile,
    "deliver": v_deliver,
    "restart-resolve": v_restart_resolve,
}


# ── job runner ───────────────────────────────────────────────────────────────

def _run_job(job_id, argv):
    log = LOG_DIR / f"job-{job_id}.log"
    with _worker_lock, open(log, "w") as f:
        f.write(f"# {_now()} {' '.join(argv)}\n")
        f.flush()
        res = subprocess.run(argv, stdout=f, stderr=subprocess.STDOUT,
                             cwd=ROOT)
    with _jobs_lock:
        _jobs[job_id]["status"] = "ok" if res.returncode == 0 else "fail"
        _jobs[job_id]["exit"] = res.returncode
        _jobs[job_id]["ended"] = _now()


def _spawn(verb, argv):
    global _seq
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with _jobs_lock:
        _seq += 1
        job_id = _seq
        _jobs[job_id] = {"id": job_id, "verb": verb, "argv": argv,
                         "status": "running", "started": _now(),
                         "log": str(LOG_DIR / f"job-{job_id}.log")}
    threading.Thread(target=_run_job, args=(job_id, argv), daemon=True).start()
    return _jobs[job_id]


# ── HTTP surface ─────────────────────────────────────────────────────────────

CONTROL_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Media Studio</title>
<style>
 body{background:#14161c;color:#eee;font:16px -apple-system,sans-serif;
      margin:0;padding:24px;max-width:640px;margin-inline:auto}
 h1{font-size:18px;letter-spacing:.2em;color:#f90;margin:0 0 16px}
 .grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
 button{padding:26px 10px;font-size:17px;font-weight:700;border:0;
        border-radius:14px;background:#262a35;color:#eee;cursor:pointer}
 button:active{transform:scale(.97)}
 .rec{background:#8c1d1d}.stop{background:#1d5c8c}.warn{background:#5a4a12}
 #st{margin-top:18px;padding:14px;background:#1b1e26;border-radius:12px;
     font:13px ui-monospace,monospace;white-space:pre-wrap;color:#9fb}
</style></head><body>
<h1>MEDIA STUDIO</h1>
<div class="grid">
 <button class="rec"  onclick="verb('record-start')">&#9679; REC</button>
 <button class="stop" onclick="verb('stop-and-ingest')">&#9632; STOP + INGEST</button>
 <button onclick="verb('ingest-last')">INGEST LAST</button>
 <button onclick="verb('ingest-screensage')">INGEST SCREENSAGE</button>
 <button onclick="refresh()">STATUS</button>
 <button class="warn" onclick="if(confirm('Restart Resolve?'))verb('restart-resolve')">RESTART RESOLVE</button>
</div>
<div id="st">loading&hellip;</div>
<script>
async function verb(name){
  const r = await fetch('/verb/'+name, {method:'POST', body:'{}'});
  document.getElementById('st').textContent = JSON.stringify(await r.json(), null, 1);
  setTimeout(refresh, 1500);
}
async function refresh(){
  try{
    const s = await (await fetch('/status')).json();
    const j = await (await fetch('/jobs')).json();
    const last = j.jobs.at(-1);
    document.getElementById('st').textContent =
      'OBS: ' + (s.obs.error ? 'unreachable' :
        (s.obs.recording ? 'RECORDING '+Math.round(s.obs.recordSeconds)+'s'
                         : 'idle @ '+s.obs.scene)) +
      '\\nResolve: ' + (s.resolve.project || s.resolve.error || s.resolve.busy) +
      (s.resolve.timeline ? ' / '+s.resolve.timeline : '') +
      '\\nLatest: ' + (s.latestRecording||'-').split('/').pop() +
      (last ? '\\nJob '+last.id+' ('+last.verb+'): '+last.status : '');
  }catch(e){ document.getElementById('st').textContent = 'daemon unreachable'; }
}
refresh(); setInterval(refresh, 5000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload, indent=1).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *a):
        pass                              # quiet; jobs have their own logs

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = CONTROL_PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/status":
            return self._send(200, v_status({}))
        if self.path == "/verbs":
            return self._send(200, {"verbs": sorted(VERBS)})
        if self.path == "/jobs":
            with _jobs_lock:
                return self._send(200, {"jobs": list(_jobs.values())[-20:]})
        if self.path.startswith("/jobs/"):
            try:
                job_id = int(self.path.split("/")[2])
            except ValueError:
                return self._send(400, {"error": "bad job id"})
            with _jobs_lock:
                job = dict(_jobs.get(job_id) or {})
            if not job:
                return self._send(404, {"error": f"no job {job_id}"})
            log = Path(job["log"])
            if log.is_file():
                job["logTail"] = log.read_text(encoding="utf-8")[-2000:]
            return self._send(200, job)
        return self._send(404, {"error": "unknown path"})

    def do_POST(self):
        if not self.path.startswith("/verb/"):
            return self._send(404, {"error": "unknown path"})
        verb = self.path.split("/", 2)[2]
        fn = VERBS.get(verb)
        if not fn:
            return self._send(404, {"error": f"unknown verb {verb!r}",
                                    "verbs": sorted(VERBS)})
        length = int(self.headers.get("Content-Length") or 0)
        try:
            args = json.loads(self.rfile.read(length)) if length else {}
        except json.JSONDecodeError:
            return self._send(400, {"error": "body must be JSON"})
        try:
            result = fn(args)
        except Exception as e:
            return self._send(500, {"error": str(e)[:300]})
        if isinstance(result, list):      # argv -> background job
            return self._send(202, _spawn(verb, result))
        return self._send(200, result)


def serve(port=PORT):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"studio daemon on http://127.0.0.1:{port}  "
          f"(verbs: {', '.join(sorted(VERBS))})")
    server.serve_forever()


if __name__ == "__main__":
    serve()
