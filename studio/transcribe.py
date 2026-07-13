"""Deepgram transcription (LOCKED doctrine: Deepgram, never Whisper).

Same call shape as bongpot's transcribe-local.mjs: nova-3, diarize, utterances.
Key from $DEEPGRAM_API_KEY or the repo .env.
"""
import json
import mimetypes
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "nova-3"
AUDIO_SIDECAR_OVER_MB = 50   # bigger media: upload only its audio track
URL = ("https://api.deepgram.com/v1/listen"
       f"?model={MODEL}&smart_format=true&punctuate=true"
       "&diarize=true&utterances=true")


class TranscribeError(RuntimeError):
    pass


def _key():
    if os.environ.get("DEEPGRAM_API_KEY"):
        return os.environ["DEEPGRAM_API_KEY"]
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("DEEPGRAM_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    raise TranscribeError("DEEPGRAM_API_KEY not in env or repo .env")


def _audio_sidecar(media_path, out_path):
    """Extract the audio track (Deepgram needs nothing else). Stream-copy if
    possible, transcode to AAC otherwise. Returns the sidecar Path."""
    audio = Path(out_path).with_name("audio.m4a")
    copy = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(media_path), "-vn",
         "-acodec", "copy", str(audio)], capture_output=True)
    if copy.returncode != 0:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(media_path), "-vn",
             "-c:a", "aac", "-b:a", "128k", str(audio)], check=True)
    return audio


def transcribe(media_path, out_path):
    """POST media to Deepgram; write {words, utterances} to out_path."""
    media_path = Path(media_path).resolve()
    if media_path.stat().st_size > AUDIO_SIDECAR_OVER_MB * 1024 * 1024:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        media_path = _audio_sidecar(media_path, out_path)
    ctype = mimetypes.guess_type(str(media_path))[0] or "application/octet-stream"
    req = urllib.request.Request(
        URL, data=media_path.read_bytes(), method="POST",
        headers={"Authorization": f"Token {_key()}", "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise TranscribeError(f"deepgram {e.code}: {e.read()[:300]}") from e

    alt = (data.get("results", {}).get("channels", [{}])[0]
               .get("alternatives", [{}])[0])
    words = alt.get("words", [])
    utterances = [
        {"id": f"u{i}", "start": u["start"], "end": u["end"],
         "text": u["transcript"], "speaker": u.get("speaker", 0),
         "confidence": u.get("confidence")}
        for i, u in enumerate(data.get("results", {}).get("utterances", []))
    ]
    out = {"model": MODEL, "words": words, "utterances": utterances}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out
