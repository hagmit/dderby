"""Verify bootstrap boundaries and the fail-closed permission configuration."""
import json
from pathlib import Path
from subprocess import run
import sys


ROOT = Path(__file__).resolve().parents[2]


def test_cli_never_claims_processing_is_active() -> None:
    result = run([sys.executable, "-m", "dderby"], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == {
        "service": "dderby", "mode": "bootstrap", "processing_enabled": False
    }


def test_permission_registry_starts_without_unidentified_channel_approval() -> None:
    registry = json.loads((ROOT / "config/permissions.json").read_text(encoding="utf-8"))
    assert registry == {"channels": []}
