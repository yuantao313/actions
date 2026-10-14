import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = yaml.safe_load((ROOT / "atomgit-checkout-pr/action.yml").read_text())["runs"]["steps"][0]["run"]


@unittest.skipUnless(os.name == "posix", "Linux Git/Bash integration")
class CheckoutTests(unittest.TestCase):
    def test_target_updates_are_used_and_stale_heads_are_rejected(self):
        for stale in [False, True]:
            with self.subTest(stale=stale), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "remote"
                source.mkdir()
                def git(*args):
                    return subprocess.check_output(["git", "-C", str(source), *args], text=True).strip()
                git("init", "-q", "-b", "main")
                git("config", "user.name", "test")
                git("config", "user.email", "test@example.invalid")
                (source / "code.cpp").write_text("base\n")
                git("add", ".")
                git("commit", "-qm", "base")
                old_base = git("rev-parse", "HEAD")
                git("checkout", "-qb", "feature")
                (source / "code.cpp").write_text("feature\n")
                git("commit", "-qam", "feature")
                head = git("rev-parse", "HEAD")
                git("update-ref", "refs/merge-requests/2/head", head)
                git("checkout", "-q", "main")
                (source / "README.md").write_text("target advanced\n")
                git("add", ".")
                git("commit", "-qm", "target advanced")
                current_base = git("rev-parse", "HEAD")
                workspace = root / "workspace"
                workspace.mkdir()
                output = root / "outputs"
                script = SCRIPT.replace('"https://atomgit.com/$PR_REPOSITORY.git"', f'"{source}"')
                result = subprocess.run(["bash", "-c", script], cwd=workspace,
                                        env={**os.environ, "GITHUB_WORKSPACE":str(workspace),
                                             "GITHUB_OUTPUT":str(output), "PR_REPOSITORY":"example/project",
                                             "PR_NUMBER":"2", "BASE_REF":"main", "HEAD_SHA":old_base if stale else head,
                                             "WORKTREE":"_source"}, text=True, capture_output=True)
                values = dict(line.split("=", 1) for line in output.read_text().splitlines())
                self.assertEqual(values["base-sha"], current_base)
                if stale:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn("worktree", values)
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual((Path(values["worktree"]) / "code.cpp").read_text(), "feature\n")
                    self.assertEqual((Path(values["worktree"]) / "README.md").read_text(), "target advanced\n")


if __name__ == "__main__":
    unittest.main()
