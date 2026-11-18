"""Import-friendly wrapper for `layer2-3.py`.

Python modules cannot be imported with a hyphen in the filename.
This wrapper loads `layer2-3.py` dynamically so the game can do:

    from game.backgrounds.layer2_3 import SchoolToUniverseTransitionBackground

without renaming the original file.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


_SRC = Path(__file__).with_name("layer2-3.py")
_SPEC = importlib.util.spec_from_file_location("game.backgrounds._layer2_3_impl", _SRC)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Failed to load {_SRC}")

_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)  # type: ignore[assignment]

# Re-export the main class we need
SchoolToUniverseTransitionBackground = _MOD.SchoolToUniverseTransitionBackground
