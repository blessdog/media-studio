import json, subprocess
BIN="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Applications/ResolveMCP"
p=subprocess.Popen([BIN],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
def rpc(o):
    p.stdin.write(json.dumps(o)+"\n"); p.stdin.flush(); return json.loads(p.stdout.readline())
rpc({"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"summer-reel","version":"0"}}})
p.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"})+"\n"); p.stdin.flush()
def run(script, i):
    r=rpc({"jsonrpc":"2.0","id":i,"method":"tools/call","params":{"name":"run_script","arguments":{"script":script,"timeout":120}}})
    return r["result"]["content"][0]["text"]
readback = r'''
tl = project.GetCurrentTimeline()
items = tl.GetItemListInTrack("video", 1)
result = {
  "page": resolve.GetCurrentPage(),
  "project": project.GetName(),
  "timeline": tl.GetName(),
  "fps": project.GetSetting("timelineFrameRate"),
  "res": [project.GetSetting("timelineResolutionWidth"), project.GetSetting("timelineResolutionHeight")],
  "v1_items": len(items),
  "a1_items": len(tl.GetItemListInTrack("audio", 1)),
  "frames": tl.GetEndFrame() - tl.GetStartFrame(),
  "markers": len(tl.GetMarkers()),
  "items": [[it.GetName(), it.GetStart() - tl.GetStartFrame(), it.GetDuration()] for it in items],
}
'''
print("READBACK", run(readback, 1))
trial = r'''
src = project.GetCurrentTimeline()
mp = project.GetMediaPool()
dup = src.DuplicateTimeline(src.GetName() + "-xfade-trial")
ok = {"duplicated": dup is not None}
if dup:
    project.SetCurrentTimeline(dup)
    items = dup.GetItemListInTrack("video", 1)
    last = items[-1]
    t = last.AddTransition({"type": "Cross Dissolve", "category": "simple", "position": "start", "alignment": "center", "duration": 20})
    ok["transition"] = None if t is None else t.GetName()
    ok["transition_frames"] = None if t is None else t.GetDuration()
    ok["modes"] = dup.GetNormalizeAudioModes()
    ok["items_after"] = len(dup.GetItemListInTrack("video", 1))
    project.SetCurrentTimeline(src)
result = ok
'''
print("TRIAL", run(trial, 2))
p.stdin.close(); p.wait(timeout=10)
