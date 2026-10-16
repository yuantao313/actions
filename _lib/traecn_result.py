"""Consume one TRAE execution's response and provenance together."""
from dataclasses import dataclass
import json
from pathlib import Path
import re


@dataclass(frozen=True)
class TraeResult:
    body: str
    model: str

    def json(self):
        return json.loads(self.body)

    @property
    def attribution(self):
        return f"\n\n<sub>By {self.model}</sub>" if self.model else ""


def load_result(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "result.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "success" or manifest.get("exit_code") != 0:
        raise ValueError("TRAE execution did not succeed")
    model = manifest.get("requested_model")
    if not isinstance(model, str) or (model and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/+-]{0,127}", model)):
        raise ValueError("Invalid requested model in TRAE result")
    response = directory / "response.md"
    if response.stat().st_size > 10485760:
        raise ValueError("Oversized TRAE response")
    body = response.read_text(encoding="utf-8")
    if not body.strip():
        raise ValueError("Empty TRAE response")
    return TraeResult(body, model)
