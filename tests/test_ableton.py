#!/usr/bin/env python3
"""Ableton .als parse gates — pipeline G2 (docs/CLIP-LANE.md §4).

    .venv/bin/python tests/test_ableton.py

Fixtures are SYNTHESISED here rather than committed: a real .als is
megabytes of Ableton factory content with its own licensing, and a
hand-built one can hit a specific trap exactly. The traps under test are
the four in studio/ableton.py's docstring, each of which produces a
plausible-looking map that is silently wrong.

The last gate runs against Ryan's own files if they are on this machine
and skips otherwise, so the suite still passes on a cold checkout.
"""
import gzip
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import ableton as abl

passed = 0
failed = 0


def check(name, ok):
    global passed, failed
    if ok:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL: {name}")


def als(body, tempo=120.0, gz=True):
    """Write a minimal but structurally faithful .als to a temp file."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Ableton MajorVersion="5" MinorVersion="12.0_12402" Creator="Ableton Live 12.4">
 <LiveSet>
  <Tracks>
{body}
  </Tracks>
  <MasterTrack>
   <DeviceChain><Mixer><Tempo>
    <Manual Value="{tempo}" />
    <ArrangerAutomation><Events>
     <FloatEvent Time="-63072000" Value="{tempo}" />
    </Events></ArrangerAutomation>
   </Tempo></Mixer></DeviceChain>
  </MasterTrack>
 </LiveSet>
</Ableton>"""
    fh = tempfile.NamedTemporaryFile(suffix=".als", delete=False)
    fh.write(gzip.compress(xml.encode()) if gz else xml.encode())
    fh.close()
    return fh.name


def midi_track(name, clips):
    return f"""   <MidiTrack>
    <Name><EffectiveName Value="{name}" /></Name>
    <DeviceChain><MainSequencer><ClipTimeable><ArrangerAutomation><Events>
{clips}
    </Events></ArrangerAutomation></ClipTimeable></MainSequencer></DeviceChain>
   </MidiTrack>"""


def midi_clip(start, end, notes, loop_on="true", loop_start=0, loop_end=4,
              start_relative=0, name="", disabled="false"):
    note_xml = "".join(
        f'<MidiNoteEvent Time="{t}" Duration="0.25" Velocity="100" />'
        for t in notes[1])
    return f"""     <MidiClip Time="{start}">
      <CurrentStart Value="{start}" /><CurrentEnd Value="{end}" />
      <Loop><LoopStart Value="{loop_start}" /><LoopEnd Value="{loop_end}" />
       <StartRelative Value="{start_relative}" /><LoopOn Value="{loop_on}" />
      </Loop>
      <Name Value="{name}" /><Disabled Value="{disabled}" />
      <Notes><KeyTracks><KeyTrack>
       <Notes>{note_xml}</Notes><MidiKey Value="{notes[0]}" />
      </KeyTrack></KeyTracks></Notes>
     </MidiClip>"""


def audio_track(name, clips):
    return f"""   <AudioTrack>
    <Name><EffectiveName Value="{name}" /></Name>
    <DeviceChain><MainSequencer><Sample><ArrangerAutomation><Events>
{clips}
    </Events></ArrangerAutomation></Sample></MainSequencer></DeviceChain>
   </AudioTrack>"""


def audio_clip(start, end, path, loop_on="false", loop_start=0, loop_end=4,
               start_relative=0, name="clip", rel="", pack="", size=0):
    return f"""     <AudioClip Time="{start}">
      <CurrentStart Value="{start}" /><CurrentEnd Value="{end}" />
      <Loop><LoopStart Value="{loop_start}" /><LoopEnd Value="{loop_end}" />
       <StartRelative Value="{start_relative}" /><LoopOn Value="{loop_on}" />
      </Loop>
      <Name Value="{name}" /><Disabled Value="false" />
      <SampleRef><FileRef>
       <Path Value="{path}" /><RelativePath Value="{rel}" />
       <RelativePathType Value="3" /><LivePackName Value="{pack}" />
       <OriginalFileSize Value="{size}" />
      </FileRef></SampleRef>
     </AudioClip>"""


# --- trap 3: Value= attributes, not element text -----------------------
p = abl.parse(als(midi_track("Drums", midi_clip(16, 24, (36, [0, 1, 2, 3])))))
check("tempo read from Manual attribute", p["tempo"] == 120.0)
clip = p["tracks"][0]["clips"][0]
check("clip start read from Value attr (not 0.0 default)",
      clip["start_beats"] == 16.0)
check("beats->secs at 120bpm: beat 16 = 8.0s", clip["start_secs"] == 8.0)
check("track name from EffectiveName", p["tracks"][0]["name"] == "Drums")
check("notes parsed with their key",
      len(clip["notes"]) == 4 and clip["notes"][0]["note"] == 36)

# --- trap 1: GroovePool clips are not music ----------------------------
groove = """  <GroovePool><Grooves><Groove><Clip><Value>
   <MidiClip Time="0">
    <CurrentStart Value="0" /><CurrentEnd Value="4" />
    <Loop><LoopStart Value="0" /><LoopEnd Value="4" /><LoopOn Value="true" />
     <StartRelative Value="0" /></Loop>
    <Notes><KeyTracks><KeyTrack>
     <Notes><MidiNoteEvent Time="0" Duration="0.0625" Velocity="100" /></Notes>
     <MidiKey Value="36" />
    </KeyTrack></KeyTracks></Notes>
   </MidiClip>
  </Value></Clip></Groove></Grooves></GroovePool>"""
xml = f"""<?xml version="1.0"?>
<Ableton MajorVersion="5" Creator="Ableton Live 12.4"><LiveSet>
 <Tracks>{audio_track("Audio", audio_clip(0, 4, "/nope.wav"))}</Tracks>
{groove}
 <MasterTrack><DeviceChain><Mixer><Tempo><Manual Value="120" />
  <ArrangerAutomation><Events><FloatEvent Time="-63072000" Value="120" />
  </Events></ArrangerAutomation></Tempo></Mixer></DeviceChain></MasterTrack>
</LiveSet></Ableton>"""
fh = tempfile.NamedTemporaryFile(suffix=".als", delete=False)
fh.write(gzip.compress(xml.encode()))
fh.close()
p = abl.parse(fh.name)
tm = abl.trigger_map(p, hash_samples=False)
check("GroovePool template contributes no clips",
      sum(len(t["clips"]) for t in p["tracks"]) == 1)
check("GroovePool template emits no phantom triggers",
      all(e["kind"] == "audio" for e in tm) and len(tm) == 1)

# --- trap 2: looped clips fire more than once --------------------------
# 16-beat span, 4-beat loop, 1 note per loop -> 4 firings, not 1.
p = abl.parse(als(midi_track("Drums",
                             midi_clip(0, 16, (36, [0]), loop_end=4))))
tm = abl.trigger_map(p, hash_samples=False)
check("looped clip expands to one entry per pass", len(tm) == 4)
check("loop passes land on the right beats",
      [e["track_start_beats"] for e in tm] == [0.0, 4.0, 8.0, 12.0])
check("beats->secs applied per firing",
      [e["track_start_secs"] for e in tm] == [0.0, 2.0, 4.0, 6.0])

# an UNLOOPED clip of the same span fires its note exactly once
p = abl.parse(als(midi_track("Drums",
                             midi_clip(0, 16, (36, [0]), loop_on="false"))))
check("unlooped clip fires once", len(abl.trigger_map(p, hash_samples=False)) == 1)

# notes past the clip's span never fire
p = abl.parse(als(midi_track("Drums",
                             midi_clip(0, 2, (36, [0, 3]), loop_on="false",
                                       loop_end=8))))
tm = abl.trigger_map(p, hash_samples=False)
check("note beyond the clip span is dropped", len(tm) == 1)

# trap 2's evil twin: notes OUTSIDE the loop brace are silent. The brace
# selects which part of the content repeats; a bare modulo would fold every
# note into the loop window and invent triggers that never sounded.
p = abl.parse(als(midi_track("Drums",
                             midi_clip(0, 8, (36, [0, 2, 5, 6]),
                                       loop_start=4, loop_end=8))))
tm = abl.trigger_map(p, hash_samples=False)
check("notes outside the loop brace never fire", len(tm) == 4)
check("only braced notes repeat, on the right beats",
      [e["track_start_beats"] for e in tm] == [1.0, 2.0, 5.0, 6.0])

# StartRelative shifts which part of the loop plays first
p = abl.parse(als(midi_track("Drums",
                             midi_clip(0, 8, (36, [0]), loop_end=4,
                                       start_relative=1))))
tm = abl.trigger_map(p, hash_samples=False)
check("StartRelative offsets the firing",
      [e["track_start_beats"] for e in tm] == [3.0, 7.0])

# looped AUDIO retriggers the sample each pass
p = abl.parse(als(audio_track("Smp", audio_clip(0, 12, "/nope.wav",
                                                loop_on="true", loop_end=4))))
tm = abl.trigger_map(p, hash_samples=False)
check("looped audio retriggers per pass", len(tm) == 3)
check("each audio pass carries its own duration",
      all(e["duration_secs"] == 2.0 for e in tm))

# --- trap 4: tempo automation is refused, not silently linearised ------
body = midi_track("Drums", midi_clip(0, 4, (36, [0])))
xml = f"""<?xml version="1.0"?>
<Ableton MajorVersion="5"><LiveSet><Tracks>{body}</Tracks>
 <MasterTrack><DeviceChain><Mixer><Tempo><Manual Value="120" />
  <ArrangerAutomation><Events>
   <FloatEvent Time="-63072000" Value="120" /><FloatEvent Time="64" Value="140" />
  </Events></ArrangerAutomation></Tempo></Mixer></DeviceChain></MasterTrack>
</LiveSet></Ableton>"""
fh = tempfile.NamedTemporaryFile(suffix=".als", delete=False)
fh.write(gzip.compress(xml.encode()))
fh.close()
try:
    abl.parse(fh.name)
    check("tempo automation refused", False)
except abl.AbletonError as exc:
    check("tempo automation refused", "tempo automation" in str(exc))

# --- refusals and hygiene ---------------------------------------------
try:
    abl.parse("/definitely/not/here.als")
    check("missing file refused", False)
except abl.AbletonError:
    check("missing file refused", True)

fh = tempfile.NamedTemporaryFile(suffix=".als", delete=False)
fh.write(b"not gzip at all")
fh.close()
try:
    abl.parse(fh.name)
    check("non-gzip file refused", False)
except abl.AbletonError as exc:
    check("non-gzip file refused", "not gzip" in str(exc))

# disabled clips never fire
p = abl.parse(als(midi_track("Drums",
                             midi_clip(0, 4, (36, [0]), disabled="true"))))
check("disabled clip emits nothing",
      abl.trigger_map(p, hash_samples=False) == [])

# session clips have no timeline position, so they have not fired
session = """   <MidiTrack>
    <Name><EffectiveName Value="S" /></Name>
    <DeviceChain><MainSequencer><ClipSlotList><ClipSlot><ClipSlot><Value>
     <MidiClip Time="0">
      <CurrentStart Value="0" /><CurrentEnd Value="4" />
      <Loop><LoopStart Value="0" /><LoopEnd Value="4" /><LoopOn Value="true" />
       <StartRelative Value="0" /></Loop>
      <Name Value="s" /><Disabled Value="false" />
      <Notes><KeyTracks><KeyTrack>
       <Notes><MidiNoteEvent Time="0" Duration="1" Velocity="100" /></Notes>
       <MidiKey Value="36" />
      </KeyTrack></KeyTracks></Notes>
     </MidiClip>
    </Value></ClipSlot></ClipSlot></ClipSlotList></MainSequencer></DeviceChain>
   </MidiTrack>"""
p = abl.parse(als(session))
check("session clip excluded by default",
      abl.trigger_map(p, hash_samples=False) == [])
check("session clip included on request",
      len(abl.trigger_map(p, hash_samples=False, include_session=True)) == 1)

# sample hashing joins to the blessdog ledger
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav:
    wav.write(b"RIFF....WAVE fake payload")
    wav_path = wav.name
p = abl.parse(als(audio_track("Smp", audio_clip(0, 4, wav_path))))
tm = abl.trigger_map(p, hash_samples=True)
check("resolvable sample carries a sha256 join key",
      tm[0]["sample_hash"] == abl.file_hash(wav_path))
p = abl.parse(als(audio_track("Smp", audio_clip(0, 4, "/gone.wav"))))
check("unresolvable sample hashes to None, still emits the firing",
      abl.trigger_map(p)[0]["sample_hash"] is None)

# --- sample resolution: the declared absolute Path is often fiction ----
# Ableton bakes its build machine into factory content, and a set that has
# moved between machines carries a stale path. The relative path is what
# actually finds the file.
tmpdir = Path(tempfile.mkdtemp())
(tmpdir / "Samples").mkdir()
real = tmpdir / "Samples" / "kick.wav"
real.write_bytes(b"x" * 1234)

als_path = tmpdir / "song.als"
als_path.write_bytes(gzip.compress(f"""<?xml version="1.0"?>
<Ableton MajorVersion="5"><LiveSet><Tracks>
{audio_track("Smp", audio_clip(0, 4, "/Volumes/data/tmp/trunk/kick.wav",
                               rel="Samples/kick.wav", size=1234))}
</Tracks>
 <MasterTrack><DeviceChain><Mixer><Tempo><Manual Value="120" />
  <ArrangerAutomation><Events><FloatEvent Time="-63072000" Value="120" />
  </Events></ArrangerAutomation></Tempo></Mixer></DeviceChain></MasterTrack>
</LiveSet></Ableton>""".encode()))
tm = abl.trigger_map(abl.parse(als_path))
check("stale absolute path falls back to project-relative",
      tm[0]["sample_resolved"] == str(real))
check("resolved sample yields the ledger join key",
      tm[0]["sample_hash"] == abl.file_hash(real))
check("declared path preserved even when it is fiction",
      tm[0]["sample_path"].startswith("/Volumes/data/tmp/trunk"))

# a same-named file of the WRONG size must not resolve: a wrong hash joins
# to the wrong sample and places the wrong video on the timeline
real.write_bytes(b"y" * 9999)
tm = abl.trigger_map(abl.parse(als_path))
check("size mismatch refuses to resolve", tm[0]["sample_resolved"] is None)
check("size mismatch yields no hash", tm[0]["sample_hash"] is None)

# --- real files, if present -------------------------------------------
REAL = [
    Path.home() / "Music/Ableton/Live Recordings/thunderdome Project/thunderdome.als",
    Path.home() / "Music/Ableton/Factory Packs/Chop and Swing/Demo Song/Clean Swing.als",
]
if all(f.is_file() for f in REAL):
    thunder = abl.parse(REAL[0])
    check("thunderdome: tempo 120", thunder["tempo"] == 120.0)
    tm = abl.trigger_map(thunder, hash_samples=False)
    check("thunderdome: exactly one firing (the VHS master), no groove notes",
          len(tm) == 1 and tm[0]["kind"] == "audio")
    check("thunderdome: the firing is the mastered VHS wav",
          "thunderdome.the.tour" in (tm[0]["sample_path"] or ""))

    swing = abl.parse(REAL[1])
    check("clean swing: tempo 82", swing["tempo"] == 82.0)
    arr = [c for t in swing["tracks"] for c in t["clips"]
           if c["view"] == "arrangement"]
    check("clean swing: 120 arrangement clips found", len(arr) == 120)
    tm = abl.trigger_map(swing, hash_samples=False)
    check("clean swing: arrangement produces a non-trivial map", len(tm) > 200)
    check("clean swing: map is sorted by time",
          all(a["track_start_secs"] <= b["track_start_secs"]
              for a, b in zip(tm, tm[1:])))
    check("clean swing: no firing before the timeline starts",
          all(e["track_start_secs"] >= 0 for e in tm))
else:
    print("  (skipped real-file gates — Ableton sets not on this machine)")

if failed:
    print(f"ABLETON FAILED ({passed} passed, {failed} failed)")
    sys.exit(1)
print(f"ABLETON OK ({passed}/{passed})")
