"""Filter only explicitly selected direct requirement lines, then invoke pip."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def filtered_lines(text, excluded):
    pattern = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:[<>=!~;\[@]|$)")
    normalized = {re.sub(r"[-_.]+", "-", name).lower() for name in excluded}
    return "".join(line for line in text.splitlines(keepends=True)
                   if not ((match := pattern.match(line)) and
                           re.sub(r"[-_.]+", "-", match.group(1)).lower() in normalized))


if __name__ == "__main__":
    source = Path(os.environ["REQUIREMENTS_FILE"]).resolve(strict=True)
    excluded = [name.strip() for name in os.environ.get("EXCLUDE_PACKAGES", "").split(",") if name.strip()]
    if not all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) for name in excluded):
        raise ValueError("Invalid excluded package name")
    if not excluded:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(source)], check=True)
    else:
        # Preserve relative -r/-c paths by keeping the temporary file beside its source.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=source.parent,
                                         prefix=".requirements-filter-", delete=False) as stream:
            stream.write(filtered_lines(source.read_text(encoding="utf-8"), excluded))
            temporary = Path(stream.name)
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(temporary)], check=True)
        finally:
            temporary.unlink(missing_ok=True)
