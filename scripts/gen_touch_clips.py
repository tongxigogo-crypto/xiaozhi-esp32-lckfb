#!/usr/bin/env python3
"""把触摸反馈用的 Ogg 短音效转成 C++ 头文件。

为什么不用 IDF 的 EMBED_FILES：
2026-11-07 试过 `_binary_<文件名>_ogg_start` 和 `_binary_assets_common_<文件名>_ogg_start`
两种符号名，云端编译两次都在链接期报 undefined reference（符号命名取决于 IDF 版本与
组件路径规则，本地没有工具链无法验证）。改成生成头文件后不再依赖链接器约定。

用法（仓库根目录）：
    python3 scripts/gen_touch_clips.py

输入：main/assets/common/touch_<kind>_<voice>.ogg
输出：main/assets/touch_clips/touch_clips.h
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "main" / "assets" / "common"
DST = ROOT / "main" / "assets" / "touch_clips" / "touch_clips.h"

KINDS = ("contact", "double", "long", "swipe")
VOICES = ("xiaohe", "yunzhou")


def c_name(kind: str, voice: str) -> str:
    return f"kTouch{kind.capitalize()}{voice.capitalize()}"


def main() -> int:
    parts = [
        "// 由 scripts/gen_touch_clips.py 生成，不要手改。",
        "// 数据来源：main/assets/common/touch_<kind>_<voice>.ogg（Ogg/Opus，16kHz 单声道）",
        "#pragma once",
        "",
        "#include <cstddef>",
        "#include <cstdint>",
        "",
        "namespace lckfb_touch::clips {",
        "",
    ]
    missing = []
    total = 0
    for kind in KINDS:
        for voice in VOICES:
            path = SRC / f"touch_{kind}_{voice}.ogg"
            if not path.exists():
                missing.append(str(path))
                continue
            data = path.read_bytes()
            total += len(data)
            parts.append(f"// {path.name}: {len(data)} bytes")
            parts.append(f"constexpr std::uint8_t {c_name(kind, voice)}[] = {{")
            for i in range(0, len(data), 16):
                chunk = ", ".join(f"0x{b:02x}" for b in data[i : i + 16])
                parts.append(f"    {chunk},")
            parts.append("};")
            parts.append("")
    parts.append("}  // namespace lckfb_touch::clips")
    parts.append("")
    parts.append(f"// 合计 {total} bytes")

    if missing:
        print("缺少素材：\n  " + "\n  ".join(missing), file=sys.stderr)
        return 1

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text("\n".join(parts), encoding="utf-8")
    print(f"已生成 {DST.relative_to(ROOT)}（{total} bytes，{len(KINDS) * len(VOICES)} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
