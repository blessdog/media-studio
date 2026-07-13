"""OBS control over obs-websocket (proven 2026-07-12).

Credentials come from OBS's own plugin config — never hardcoded. Known
failure mode: a stream output stopped mid-reconnect wedges OBS (ignores
websocket + SIGTERM); remedy is SIGKILL + relaunch in Normal Mode.
"""
import json
from pathlib import Path

WS_CONFIG = Path.home() / ("Library/Application Support/obs-studio/"
                           "plugin_config/obs-websocket/config.json")


class OBSUnavailable(RuntimeError):
    pass


def client(timeout=5):
    try:
        import obsws_python as obs
        cfg = json.loads(WS_CONFIG.read_text(encoding="utf-8"))
        return obs.ReqClient(host="localhost", port=cfg["server_port"],
                             password=cfg["server_password"], timeout=timeout)
    except Exception as e:
        raise OBSUnavailable(f"OBS websocket unreachable: {e}") from e


def status():
    cl = client()
    rec = cl.get_record_status()
    st = cl.get_stream_status()
    scene = cl.get_current_program_scene()
    return {
        "recording": bool(rec.output_active),
        "recordSeconds": getattr(rec, "output_duration", 0) / 1000,
        "streaming": bool(st.output_active),
        "streamReconnecting": bool(st.output_reconnecting),
        "scene": scene.scene_name,
    }


def start_record():
    client().start_record()


def stop_record():
    """Stop recording. Returns the finished file's path."""
    return client().stop_record().output_path
