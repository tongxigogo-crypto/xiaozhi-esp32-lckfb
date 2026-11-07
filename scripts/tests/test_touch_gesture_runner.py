import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEST_SOURCE = ROOT / "scripts" / "tests" / "touch_gesture_test.cc"
FEEDBACK_SOURCE = (
    ROOT / "main" / "boards" / "lckfb" / "szpi-esp32s3" / "touch_feedback.cc"
)


class TouchGestureRunnerTest(unittest.TestCase):
    def test_touch_gesture_behavior(self):
        candidates = []
        configured = os.environ.get("CXX")
        if configured:
            candidates.append(configured)
        candidates.extend(("c++", "g++", "clang++"))
        compiler = next((shutil.which(candidate) for candidate in candidates if shutil.which(candidate)), None)
        if compiler is None:
            self.skipTest("no host C++ compiler is available")

        with tempfile.TemporaryDirectory(prefix="xiaozhi-touch-") as temp_dir:
            executable = Path(temp_dir) / "touch_gesture_test"
            command = [
                compiler,
                "-std=c++17",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(TEST_SOURCE),
                str(FEEDBACK_SOURCE),
                "-o",
                str(executable),
            ]
            subprocess.run(command, cwd=ROOT, check=True)
            subprocess.run([str(executable)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
