# LCKFB 小肥鱼 v2.5.3

本板构建开启 `USE_EMOTE_MESSAGE_STYLE` 和 `FLASH_EXPRESSION_ASSETS`，保留设备 AEC、ES7210 MIC1 28dB 及既有音频引脚。

## 表情与触摸

`assets/pufferfish` 含 24 个静态 EAF 表情，每个为 320×240 黑底画布，角色位于中央 160×160 区域。两个相同完整帧兼容播放器的帧计数约定；这是第一批静态表情，不是呼吸或嘴型动画。`assets/320_240/emote.json` 注册原始 24 个 ID，并为既有协议表情提供别名。

触摸 INT 为 NC。独立优先级 1 FreeRTOS 任务每 40ms 读取 FT5x06，读取失败不会合成松手；非表情模式仍使用原 LVGL 路径。

| 手势 | 条件 | 表情 |
| --- | --- | --- |
| 单击 | 接触少于 300ms、位移不超过 10px；等待双击窗口结束 | happy |
| 双击 | 两次合格单击位于 500ms 窗口内 | surprised |
| 长按 | 至少 1200ms，位移不超过 10px | annoyed |
| 左右滑 | 横向位移大于 40px，纵向位移不超过 40px | laugh |

## 电量接口

外挂 2000mAh 升压背板仅向 VBUS 供电，没有连接 ADC。当前无采样时默认隐藏电量文本，不估算或伪造数值。

未来代码可通过 `EmoteDisplay::SetBatteryLevel(level, charging)` 传入真实值。0–100 为有效值，负数或超过 100 时隐藏；有效的 0 会显示 `0%`。有效值同步发送 `EMOTE_MGR_EVT_BAT`；无效值不会发送给会把负数裁剪为 0 的组件。右上角仅显示浅色半透明百分比，保留组件电量标签默认的 12px 小字号，无电池图标。

## 资源重建

`scripts/encode_pufferfish_eaf.py` 将已确认的 24 张 320×240 PNG 编成 8bit BGRA 调色板、分块 RLE EAF。先 alpha 合成到黑底，再以 MEDIANCUT/256 色/no dither 量化。离线转换不依赖在线转换服务。输入目录只放 24 张表情 PNG，不包含预览表。

```sh
python scripts/encode_pufferfish_eaf.py PNG_DIRECTORY EAF_DIRECTORY
python -m unittest scripts.tests.test_pufferfish_eaf -v
python -m unittest scripts.tests.test_touch_gesture_runner -v
python scripts/build.py lckfb/szpi-esp32s3 --name lichuang-dev --wake-word disabled
```

## OTA 交付

Actions 产出 `xiaozhi.bin`、`expression_assets.bin` 和 SHA256 清单。将 **xiaozhi.bin** 另存为 **lichuang-dev_2.5.3.bin** 供应用 OTA；不要把 merged-binary.bin 当作应用 OTA 镜像。

**应用 OTA 不会自动写入独立的 assets 分区。** 首次从普通 LCD 模式升级时，还必须通过现有资源更新通道或独立的授权烧录步骤更新 `expression_assets.bin`，才能显示本批小肥鱼表情。默认 16MB 分区表的 assets 偏移为 0x800000、大小 8MiB；实际操作前必须确认实机分区表。本次代码提交/云编译不刷写设备。

构建成功只证明编译与打包完成。触摸方向、连续操作、显示效果和音频收放仍需实机验证。
