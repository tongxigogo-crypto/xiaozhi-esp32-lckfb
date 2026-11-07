import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_SOURCE = ROOT / "scripts" / "tests" / "test_ui_sound_arbiter.cc"


class UiSoundArbiterRunnerTest(unittest.TestCase):
    def test_ui_sound_arbiter(self):
        candidates = []
        configured = os.environ.get("CXX")
        if configured:
            candidates.append(configured)
        candidates.extend(("c++", "g++", "clang++"))
        compiler = next(
            (shutil.which(c) for c in candidates if shutil.which(c)), None
        )
        if compiler is None:
            self.skipTest("no host C++ compiler is available")

        with tempfile.TemporaryDirectory(prefix="xiaozhi-arbiter-") as temp_dir:
            executable = Path(temp_dir) / "ui_sound_arbiter_test"
            subprocess.run(
                [
                    compiler,
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    str(TEST_SOURCE),
                    "-o",
                    str(executable),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(executable)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
