"""Bundle-local prompt agent for the anime action lexicon.

Reads the bundle's SQLite catalog read-only, checks an IR against the bundle's
own composition rules plus a priority/budget policy, and projects the IR to
prose. Nothing here renders or calls a model.
"""
import importlib.util
import sys
from pathlib import Path

__version__ = "0.1.0"

AGENT_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = AGENT_DIR.parent
DATA_DIR = AGENT_DIR / "data"
CANONICAL_FINGERPRINT = "275537d8f7c8d4bcb5a82c0d28ccf7efb5e6f6c3b8153ae35fecd971f99df639"


def bundle_validator():
    """Import the bundle's validate_anime_seed.py as a module (its main() is guarded)."""
    name = "validate_anime_seed"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, BUNDLE_DIR / "validate_anime_seed.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


seed = bundle_validator()
SLOTS = frozenset(seed.SLOTS)
MOMENTS = frozenset(seed.MOMENTS)
GLOBAL_SLOTS = frozenset(seed.GLOBAL_SLOTS)
PLACEHOLDER = seed.PLACEHOLDER
COLUMNS = tuple(seed.COLUMNS)
