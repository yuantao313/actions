from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_every_stage_parses_and_has_explicit_shells(self):
        actions = list(ROOT.glob("*/action.yml"))
        self.assertEqual(len(actions), 11)
        for path in actions:
            with self.subTest(stage=path.parent.name):
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertEqual(data["runs"]["using"], "composite")
                for step in data["runs"]["steps"]:
                    if "run" in step:
                        self.assertIn("shell", step)

    def test_no_project_routes_or_old_platform_names_in_runtime_code(self):
        files = [*ROOT.glob("*/action.yml"), *ROOT.glob("_lib/*.py"), *ROOT.glob("*/*.sh"), *ROOT.glob("*/*.py")]
        for path in (p for p in files if p.parent.name != "tests"):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                for forbidden in ["cann/catlass", "ascend-catlass", "gitcode.com", "GITCODE_TOKEN"]:
                    self.assertNotIn(forbidden, text)

    def test_traecn_invokes_the_cli_without_external_wrapper(self):
        data = yaml.safe_load((ROOT / "traecn/action.yml").read_text())
        script = data["runs"]["steps"][0]["run"]
        self.assertNotIn("python", script)
        self.assertNotIn("run.py", script)
        self.assertIn("--ask-for-approval never exec", script)
        self.assertFalse((ROOT / "traecn/run.py").exists())

    def test_public_catalog_contains_only_general_stages(self):
        expected = {
            "atomgit-api", "atomgit-pr-metadata", "atomgit-checkout-pr",
            "atomgit-pr-status", "atomgit-issue-context", "atomgit-issue-comment",
            "atomgit-release", "setup-traecn", "traecn",
            "install-python-requirements", "trust-checkout",
        }
        self.assertEqual({p.parent.name for p in ROOT.glob("*/action.yml")}, expected)


if __name__ == "__main__":
    unittest.main()
