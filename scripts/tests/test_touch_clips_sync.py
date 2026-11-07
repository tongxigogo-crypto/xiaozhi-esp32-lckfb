"""校验 main/assets/touch_clips/touch_clips.h 与 assets/common 下的 ogg 源素材一致。

生成头文件是构建输入，源素材才是真值；两者漂移会让板子播放旧音效却没人发现。
CI 里跑一次，本地改素材后忘了重跑脚本会被这个测试拦下。
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "main" / "assets" / "common"
HEADER = ROOT / "main" / "assets" / "touch_clips" / "touch_clips.h"

KINDS = ("contact", "double", "long", "swipe")
VOICES = ("xiaohe", "yunzhou")

ARRAY_RE = re.compile(
    r"constexpr std::uint8_t\s+(kTouch\w+)\[\]\s*=\s*\{(.*?)\};", re.DOTALL
)


def array_name(kind: str, voice: str) -> str:
    return f"kTouch{kind.capitalize()}{voice.capitalize()}"


def parse_header() -> dict:
    text = HEADER.read_text(encoding="utf-8")
    result = {}
    for name, body in ARRAY_RE.findall(text):
        values = bytes(int(token, 16) for token in re.findall(r"0x([0-9a-fA-F]{2})", body))
        result[name] = values
    return result


class TouchClipsSyncTest(unittest.TestCase):
    def test_header_matches_sources(self):
        self.assertTrue(HEADER.exists(), f"缺少生成文件：{HEADER}")
        arrays = parse_header()
        for kind in KINDS:
            for voice in VOICES:
                source = ASSETS / f"touch_{kind}_{voice}.ogg"
                self.assertTrue(source.exists(), f"缺少素材：{source}")
                name = array_name(kind, voice)
                self.assertIn(name, arrays, f"头文件缺少数组：{name}")
                self.assertEqual(
                    arrays[name],
                    source.read_bytes(),
                    f"{name} 与 {source.name} 不一致，请重跑 python3 scripts/gen_touch_clips.py",
                )

    def test_header_declares_expected_count(self):
        arrays = parse_header()
        self.assertEqual(len(arrays), len(KINDS) * len(VOICES))


if __name__ == "__main__":
    unittest.main()
