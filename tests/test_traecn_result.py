import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from _lib.traecn_result import load_result
from _lib import operations


class ResultTests(unittest.TestCase):
    def write_result(self, directory, model="provider/new-model", status="success", code=0):
        root = Path(directory)
        (root / "result.json").write_text(json.dumps({"status": status, "exit_code": code,
                                                     "requested_model": model}), encoding="utf-8")
        (root / "response.md").write_text("A useful reply", encoding="utf-8")

    def test_provenance_changes_with_execution_without_formatter_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            for model in ("provider/new-model", "other-model", ""):
                self.write_result(directory, model)
                result = load_result(directory)
                self.assertEqual(result.body, "A useful reply")
                self.assertEqual(result.attribution, f"\n\n<sub>By {model}</sub>" if model else "")

    def test_failed_missing_or_invalid_results_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for model, status, code in [("model", "failed", 1), ("model", "success", 124), ("<script>", "success", 0)]:
                self.write_result(directory, model, status, code)
                with self.assertRaises(ValueError):
                    load_result(directory)
            self.write_result(directory)
            (Path(directory) / "response.md").unlink()
            with self.assertRaises(FileNotFoundError):
                load_result(directory)

    def test_comment_consumes_one_stage_result_and_rejects_conflicting_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            self.write_result(directory)
            context = Path(directory) / "context.json"
            context.write_text("{}")
            env = {"ATOMGIT_TOKEN": "test-only", "ACTION_OPERATION": "comment", "TRAE_RESULT": directory, "CONTEXT_FILE": str(context),
                   "BODY_FILE": "", "MODEL_ID": "", "RESULT_FILE": str(Path(directory) / "published.json"),
                   "GITHUB_OUTPUT": str(Path(directory) / "output")}
            with patch.dict(os.environ, env), patch.object(operations, "comment", return_value={}) as comment:
                operations.main()
                self.assertEqual(comment.call_args.args[2:4], ("A useful reply", "provider/new-model"))
            with patch.dict(os.environ, dict(env, MODEL_ID="conflicting")), patch.object(operations, "comment") as comment:
                with self.assertRaisesRegex(ValueError, "cannot be combined"):
                    operations.main()
                comment.assert_not_called()
