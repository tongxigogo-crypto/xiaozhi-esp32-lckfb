import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEST_SOURCE = ROOT / "scripts" / "tests" / "test_connection_recovery_policy.cc"
POLICY_SOURCE = ROOT / "main" / "protocols" / "connection_recovery.cc"


class ConnectionRecoveryPolicyRunnerTest(unittest.TestCase):
    def test_connection_recovery_policy(self):
        candidates = []
        configured = os.environ.get("CXX")
        if configured:
            candidates.append(configured)
        candidates.extend(("c++", "g++", "clang++"))
        compiler = next(
            (shutil.which(candidate) for candidate in candidates if shutil.which(candidate)),
            None,
        )
        if compiler is None:
            self.skipTest("no host C++ compiler is available")

        with tempfile.TemporaryDirectory(prefix="xiaozhi-recovery-") as temp_dir:
            executable = Path(temp_dir) / "connection_recovery_policy_test"
            subprocess.run(
                [
                    compiler,
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    str(TEST_SOURCE),
                    str(POLICY_SOURCE),
                    "-o",
                    str(executable),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(executable)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
