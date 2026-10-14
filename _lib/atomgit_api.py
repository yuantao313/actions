"""Shared authenticated AtomGit REST transport and generic action entrypoint."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import urllib.error
import urllib.parse
import urllib.request

API_ROOT = "https://api.atomgit.com/api/v5"


class AtomGitAPI:
    def __init__(self, token):
        if not token:
            raise ValueError("AtomGit token is required")
        self.headers = {"Authorization": f"Bearer {token}", "PRIVATE-TOKEN": token,
                        "Accept": "application/json", "User-Agent": "yuantao313-actions"}

    def request(self, method, path, body=None, encoding="form"):
        if method not in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
            raise ValueError("Unsupported AtomGit method")
        if not path.startswith("/") or path.startswith("//") or ".." in path or "\n" in path:
            raise ValueError("AtomGit path must be relative to the fixed v5 API root")
        if encoding not in {"form", "json"}:
            raise ValueError("Body encoding must be form or json")
        headers, data = dict(self.headers), None
        if body is not None:
            if not isinstance(body, (dict, list)) or (isinstance(body, dict) and "access_token" in body):
                raise ValueError("Request body must be JSON data without credentials")
            if encoding == "json":
                data = json.dumps(body).encode("utf-8")
                headers["Content-Type"] = "application/json"
            else:
                if not isinstance(body, dict):
                    raise ValueError("Form data must be an object")
                data = urllib.parse.urlencode(body).encode("utf-8")
                headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(API_ROOT + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                content = response.read()
                # AtomGit PATCH/DELETE may succeed with HTTP 204 or an empty
                # response. Business stages verify mutations with a separate GET.
                return json.loads(content) if content.strip() else {}
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"AtomGit {method} request failed (HTTP {error.code})") from None


def main():
    body_file = os.environ.get("ATOMGIT_API_BODY", "")
    body = json.loads(Path(body_file).read_text(encoding="utf-8")) if body_file else None
    result = AtomGitAPI(os.environ.get("ATOMGIT_TOKEN", "")).request(
        os.environ["ATOMGIT_API_METHOD"], os.environ["ATOMGIT_API_PATH"], body,
        os.environ.get("ATOMGIT_API_ENCODING", "form"))
    directory = Path(tempfile.mkdtemp(prefix="atomgit-api-", dir=os.environ.get("RUNNER_TEMP")))
    output = directory / "response.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
        stream.write(f"response-file={output}\n")
    print("AtomGit API request completed")


if __name__ == "__main__":
    main()
