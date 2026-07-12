"""Single place that knows how to reach DaVinci Resolve's scripting API.

Every tool imports connect() from here instead of exporting env vars by hand.
"""
import os
import sys

_API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
_LIB = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
_MODULES = os.path.join(_API, "Modules")


class ResolveUnavailable(RuntimeError):
    pass


def connect():
    """Return the Resolve app object or raise ResolveUnavailable."""
    os.environ.setdefault("RESOLVE_SCRIPT_API", _API)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", _LIB)
    if _MODULES not in sys.path:
        sys.path.insert(0, _MODULES)
    try:
        import DaVinciResolveScript as dvr
    except ImportError as e:
        raise ResolveUnavailable(f"scripting module not importable: {e}") from e
    app = dvr.scriptapp("Resolve")
    if app is None:
        raise ResolveUnavailable(
            "Resolve is not answering. Is it running, with Preferences > "
            "System > General > External scripting = Local?"
        )
    return app


def current_or_named_project(app, name):
    """Load `name` if it exists, else the current project, else create `name`."""
    pm = app.GetProjectManager()
    proj = pm.LoadProject(name) or pm.GetCurrentProject() or pm.CreateProject(name)
    if not proj:
        raise ResolveUnavailable(
            f"could not load or create project {name!r} (Project Manager modal open?)"
        )
    return proj
