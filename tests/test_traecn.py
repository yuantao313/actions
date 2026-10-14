import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = yaml.safe_load((ROOT / "traecn/action.yml").read_text())["runs"]["steps"][0]["run"]


@unittest.skipUnless(os.name == "posix", "Linux shell and timeout integration")
class TraeTests(unittest.TestCase):
    def run_case(self, override=None, fake_status=0):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tree = root / "workspace"
            tree.mkdir()
            (tree / ".git").mkdir()
            cli = root / "traecli"
            cli.write_text('''#!/usr/bin/env bash
set -euo pipefail
case "$1" in
  --version) echo 'traecli 0.209.1'; exit 0 ;;
  exec) echo '--json --output-last-message --ephemeral --ignore-user-config'; exit 0 ;;
  login) [[ "$TRAECLI_PERSONAL_ACCESS_TOKEN" == test-pat ]]; touch "$HOME/credential"; exit 0 ;;
esac
[[ "$1" == --ask-for-approval && "$2" == never && "$3" == exec ]]
[[ -z "${TRAECLI_PERSONAL_ACCESS_TOKEN:-}" && -z "${TRAE_PAT:-}" && -z "${GITHUB_TOKEN:-}" && -z "${ATOMGIT_TOKEN:-}" ]]
[[ -f "$HOME/credential" ]]
printf '%s' "$HOME" > "$(dirname "$0")/auth-path"
cat > "$(dirname "$0")/received-prompt"
while [[ $# -gt 0 ]]; do
  if [[ "$1" == --output-last-message ]]; then shift; response=$1; fi
  shift
done
printf '%s\\n' 'A final answer with test-pat' > "$response"
echo '{"event":"done","text":"test-pat"}'
exit ''' + str(fake_status) + '\n')
            cli.chmod(0o755)
            prompt = '中文提示\n$(touch forbidden)\n::error::literal'
            env = {**os.environ, "RUNNER_TEMP": str(root), "GITHUB_WORKSPACE": str(tree),
                   "GITHUB_OUTPUT": str(root / "output"), "TRAE_PAT": "test-pat", "TRAE_PROMPT": prompt,
                   "TRAE_PROMPT_FILE": "", "TRAE_WORKDIR": ".", "TRAE_CLI": str(cli),
                   "TRAE_VERSION": "0.209.1", "TRAE_MODEL": "raw-model-id", "TRAE_HOST": "",
                   "TRAE_SANDBOX": "read-only", "TRAE_SCHEMA": "", "TRAE_TIMEOUT": "10",
                   "GITHUB_TOKEN": "must-not-inherit", "ATOMGIT_TOKEN": "must-not-inherit"}
            env.update(override or {})
            result = subprocess.run(["bash", "-c", SCRIPT], env=env, text=True, capture_output=True)
            artifacts = list(root.glob("traecn-result.*"))
            manifest = json.loads((artifacts[0] / "result.json").read_text()) if artifacts else {}
            if result.returncode == 0:
                self.assertEqual((root / "received-prompt").read_text(), prompt)
                self.assertNotIn("test-pat", (artifacts[0] / "response.md").read_text())
                self.assertNotIn("test-pat", (artifacts[0] / "events.jsonl").read_text())
                self.assertFalse(Path((root / "auth-path").read_text()).exists())
            self.assertFalse(list(root.glob("traecn-auth.*")))
            return result, manifest

    def test_literal_stdin_credentials_cleanup_and_redaction(self):
        result, manifest = self.run_case()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(manifest["status"], "success")
        self.assertEqual(manifest["requested_model"], "raw-model-id")

    def test_nonzero_cli_exit_fails_stage(self):
        result, manifest = self.run_case(fake_status=9)
        self.assertEqual(result.returncode, 9)
        self.assertEqual(manifest["status"], "failed")

    def test_invalid_input_fails_before_execution(self):
        for override in [{"TRAE_PAT": ""}, {"TRAE_SANDBOX": "danger-full-access"}, {"TRAE_TIMEOUT": "0"},
                         {"TRAE_VERSION": "9.9.9"}, {"TRAE_PROMPT_FILE": "also-provided"}]:
            with self.subTest(override=override):
                result, manifest = self.run_case(override)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(manifest["status"], "failed")


if __name__ == "__main__":
    unittest.main()
