import json, subprocess, sys, time
BIN="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Applications/ResolveMCP"
p=subprocess.Popen([BIN],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def send(o):
    p.stdin.write(json.dumps(o)+"\n"); p.stdin.flush()
def recv():
    line=p.stdout.readline()
    return json.loads(line) if line.strip() else None
send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}})
r=recv(); print("initialize ->", json.dumps(r)[:600])
send({"jsonrpc":"2.0","method":"notifications/initialized"})
send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_resolve_status","arguments":{}}})
print("status ->", json.dumps(recv())[:500])
script = """
pm = resolve.GetProjectManager()
proj = pm.GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None
result = {
  "page": resolve.GetCurrentPage(),
  "version": resolve.GetVersionString(),
  "project": proj.GetName() if proj else None,
  "timeline": tl.GetName() if tl else None,
  "timelines": proj.GetTimelineCount() if proj else None,
}
"""
send({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"run_script","arguments":{"script":script}}})
print("run_script ->", json.dumps(recv())[:900])
send({"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"run_script","arguments":{"script":"import os\nresult=os.getcwd()"}}})
print("sandbox os ->", json.dumps(recv())[:400])
send({"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"search_scripting_api","arguments":{"pattern":"GetTranscription"}}})
print("search ->", json.dumps(recv())[:700])
p.stdin.close(); p.wait(timeout=10); print("stderr:", p.stderr.read()[:500])
