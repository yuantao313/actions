import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("requirements_stage", ROOT / "install-python-requirements/install.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class RequirementTests(unittest.TestCase):
    def test_direct_exclusions_preserve_other_packages_and_pip_controls(self):
        text = "torch==2.7\nTorch_NPU>=2.7\nlit\ntorchvision>=0.20\nnumpy>=1.21\n-r nested.txt\n--index-url https://example.invalid/simple\n# torch is provisioned\n"
        result = module.filtered_lines(text, ["torch", "torch-npu", "lit"])
        self.assertEqual(result, "torchvision>=0.20\nnumpy>=1.21\n-r nested.txt\n--index-url https://example.invalid/simple\n# torch is provisioned\n")

    def test_no_default_exclusions(self):
        text = "torch==2.7\nlit\nnumpy\n"
        self.assertEqual(module.filtered_lines(text, []), text)


if __name__ == "__main__":
    unittest.main()
