"""Exercise the actual main/CMakeLists external-assets dependency block."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("cmake"), "cmake unavailable; run with uv --with cmake")
class EmoteAssetDependencyTests(unittest.TestCase):
    def test_eaf_and_manifest_changes_rebuild_binary(self):
        source = (ROOT / "main/CMakeLists.txt").read_text()
        block = re.search(r"            # The component command tracks its script only.*?            add_custom_command\(OUTPUT \$\{ASSETS_FILE\} APPEND\n                DEPENDS \$\{EMOTE_EXTERNAL_INPUTS\}\n            \)", source, re.S)
        self.assertIsNotNone(block)
        with tempfile.TemporaryDirectory(prefix="eaf-cmake-") as tmp:
            root = Path(tmp)
            inputs = root / "assets"
            inputs.mkdir()
            image = inputs / "test.eaf"
            image.write_bytes(b"first")
            manifest = inputs / "emote.json"
            manifest.write_text("[]")
            (root / "CMakeLists.txt").write_text("""
cmake_minimum_required(VERSION 3.20)
project(eaf_dependency_test NONE)
set(EMOTE_EXTERNAL_PATH "${CMAKE_CURRENT_SOURCE_DIR}/assets")
set(ASSETS_FILE "${CMAKE_BINARY_DIR}/expression_assets.bin")
add_custom_command(OUTPUT ${ASSETS_FILE}
    COMMAND "${CMAKE_COMMAND}" -E touch "${ASSETS_FILE}")
""" + block.group(0) + """
add_custom_target(assets ALL DEPENDS ${ASSETS_FILE})
""")
            build = root / "build"
            subprocess.run(["cmake", "-S", str(root), "-B", str(build)], check=True, capture_output=True)
            def run():
                subprocess.run(["cmake", "--build", str(build)], check=True, capture_output=True)
                return (build / "expression_assets.bin").stat().st_mtime_ns
            first = run()
            self.assertEqual(first, run(), "unchanged inputs should not rebuild")
            time.sleep(1.05)
            image.write_bytes(b"second")
            second = run()
            self.assertGreater(second, first, "EAF edit must regenerate binary")
            time.sleep(1.05)
            manifest.write_text('[{"src":"test.eaf"}]')
            self.assertGreater(run(), second, "emote manifest edit must regenerate binary")


if __name__ == "__main__":
    unittest.main()
