# 给其他 Agent 的同步说明

> 读这一页就够，不要再去猜基线。
> 生成时间：2026-11-05 17:36｜生成者：小马（WorkBuddy）

---

## 一、基线在哪

```
仓库  tongxigogo-crypto/xiaozhi-esp32-lckfb
分支  wip/2.5.4-baseline
HEAD  以 git rev-parse --short fork/wip/2.5.4-baseline 为准
      内容基线起点 72690ca（首个固化提交）
```

**这是唯一有效基线。** 之前的一切说法作废：

| 作废对象 | 原因 |
| :--- | :--- |
| `feat/emote-touch-battery`（`d26086a`） | 功能被 `91e9bc2` 覆盖，分支已删，仅存 tag `archive/emote-touch-battery-d26086a` |
| 远端 `main`（`bda9bff`） | 落后基线 2 个提交 |
| 工作区未提交改动 | 已全部固化进 `72690ca` |
| 任何"当前是 2.5.3"的说法 | 2.5.3 已被烧过一版，下一版是 **2.5.4** |

## 二、基线里有什么

| 项 | 状态 |
| :--- | :--- |
| 表情模式 | 已开（`CONFIG_USE_EMOTE_MESSAGE_STYLE=y`） |
| 触摸手势 | 已实现，`touch_gesture.h` 模块化，40ms 轮询 / 双击 500ms / 长按 1200ms / 横滑 40px |
| 河豚资源 | 24 个 eaf 已入仓，`emote.json` 登记，fps 12 |
| 电量接口 | 已写，但板子无采样电路 → 永远走"无值不显示"分支 |
| 版本号 | `2.5.3`（**尚未改成 2.5.4**） |
| 服务端 | 未动，仍指内网 `192.168.*` |

## 三、开工前必须做的三件事

**1. 报基线。** 先跑这三条，把原文贴出来：

```bash
git rev-parse --short HEAD
git status --porcelain | wc -l
git rev-parse --short fork/wip/2.5.4-baseline
```

`dirty` 不为 0 → 不许开工，先提交或 stash。HEAD 不等于基线 → 说明你在别的版本上，先确认。

**2. 认领。** 改代码前在 `.agent/PROJECT_STATE.md` 的租约表里登记：区域 / 名字 / 起始 / 到期。同一区域同时只允许一个 Agent。

**3. 带标识。** 提交信息末尾加 `[agent:<名字>]`。

**4. 编译权归小马。** 写完代码交付分支就停，不要自己触发 `build-lckfb.yml`、不要下载产物。编译在审查通过后统一发起。

也可以直接跑守卫：

```bash
./scripts/agent_guard.sh
```

## 四、绝对不要碰

| 对象 | 原因 |
| :--- | :--- |
| `main/application.cc` 的 `kSecurityLicenseAnchor` | 删了固件死循环 |
| `xiaozhi-esp32-server/main/xiaozhi-server/models/` | 903MB 模型 |
| `data/.config.yaml` | 含 API Key，改配置找小马 |
| `firmware_bin/merged-binary.bin` | 11-03 的 2.5.2 旧包，不含表情，烧了会退版 |
| 已在跑的 frps（VPS）与 frpc（Mac） | 小马独占 |

## 五、五个已知坑

1. **assets 分区只有 8MB**，`emoji_large` 已 5.4MB，加字体后约 7MB。再加表情就爆。
2. **OTA 不写 assets 分区**。资源变了必须单独写 `0x800000`，只 OTA `xiaozhi.bin` 会黑屏。
3. **`assets/pufferfish/` 与 `assets/emoji_large/` 内容重复**，打包只用后者，前者待删。
4. **服务端 `vision_explain` 与 `websocket` 仍是内网地址**，出门必挂，要改成公网 `47.117.142.184`。
5. **`merged-binary.bin` 是 2.5.2**，和 `xiaozhi.bin`（2.5.3）混版，不能成套使用。

## 六、待办分工

**代码由编码 Agent 写，小马只出规格与审查。** 规格见 `.agent/SPEC-2.5.4.md`。

| 事项 | 归属 | 状态 |
| :--- | :--- | :--- |
| T1–T5 固件改动（OTA 地址、EraseKey、NVS 清理、版本号、产物清单） | 编码 Agent | 规格已出，待写 |
| 服务端 `vision_explain` / 鉴权 | 小马 | 待做 |
| frpc 常驻（LaunchAgent） | 小马 | 待做 |
| 表情体积压缩（220KB → 目标 140KB） | 待定 | 等决策 |
| 电量硬件方案 | 老大 | 等拍板 |
| 一次编译出 2.5.4 | 小马 | 阻塞于 T1–T5 完成 |

## 七、审查怎么做

见 `.agent/REVIEW_PROTOCOL.md`。核心一条：**只审 `wip/2.5.4-baseline` 的当前 HEAD，不审工作区。**

审查结论请落到 `docs/review/72690ca-<你的名字>.md`，格式：必须改 / 建议改 / 可忽略，每条带证据（文件:行 或 命令输出）。

## 最新用户授权（2026-11-05T18:24:21+08:00，优先于本文历史职责限制）

开发、测试、配置修复、构建和烧录准备统一由 Codex 完成；独立审查由 Gemini 完成。T7 相机工具注册并入 2.5.4，表情资源执行有备份的压缩优化。允许为本轮准备触发候选构建、下载和校验产物；不代表已经批准实际烧录或公开发布。保留模型与原始素材；密钥只存私密配置，禁止写入提交、文档和日志。

## 2026-11-05T19:50:56+0800 实施收口同步

开发分支feat/2.5.4-ota-public；功能提交3672528经Gemini3.8Flash（Antigravity）PASS，报告docs/review/2.5.4-gemini-3.8-flash.md。后续证据/状态提交不改main/scripts/workflow。先读STATUS首节，最终产物读项目outputs/2.5.4-final/latest-release.json。禁止从历史main或旧merged推断当前可烧版本。真正烧录和OTA公开发布仍未执行。


## 2026-11-06T08:36:58.538168+08:00 2.5.6软件准备完成，待用户验收页审查/最终烧录确认

- 固件33d7bdf / 分支codex/2.5.6-completion；服务端95a9fff。用户最近明确：无真实电量继续隐藏，200–210ms范围允许5FPS200ms；情绪符号指原画爱心/问号/怒气。
- 28px标签修复真实字体25px高度裁剪，状态空闲/聆听中/说话中；显式情绪与说话状态先后顺序均通过，下一轮清理。24套无损压缩保留原像素，非重绘声明。
- Gemini3.8Flash(Antigravity)三范围PASS；独立固件147PASS5预期skip/服务端78PASS/人设14/情绪65案例。最终资源包24套168帧官方C/Python/源manifest一致，10字形齐全。
- Actions42136258139 SUCCESS，四文件已在Mac+Windows项目outputs/2.5.6-completion/artifact-33d7bdf；应用2.5.6/2685056字节，资源6192626字节。latest-release.json为产物身份真值；后续文档HEAD不冒充编译SHA。
- 正式服务已切至版本化server-95a9fff，私密配置备份，固定鉴权/TLS/控制工具确认规则保留。真实模型3情绪+两工具+thinking续接通过，未把思考/密钥写进证据。
- 单文件验收页outputs/2.5.6-completion/acceptance/index.html与人类操作手册xiaofeiyu_2.5.6_acceptance.md已备；网页不是液晶实拍/声音验收。
- 本轮未烧录、未发布OTA、未合并main。旧96fada8配对app/assets及全量私密备份保留；等用户明确确认再写设备。板上最新已核实仍2.5.5。此条优先于本文件早期2.5.4/未加固/未轮换等历史状态。
- Actor Codex，证据docs/review/2.5.6-gemini-review.md、项目outputs/2.5.6-completion/evidence。历史提交33d7bdf/95a9fff由Codex集成；后续提交带agent标识，不改写已构建提交。
