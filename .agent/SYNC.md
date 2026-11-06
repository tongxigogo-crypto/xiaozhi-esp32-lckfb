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


## 2026-11-06T08:46:48.721424+08:00 2.5.6候选修正正在重编

- 验收页发现150px状态黑底遮住部分爱心/问号；已缩窄72px，实际文字宽38/58/57px。Gemini显示复审PASS，独立QA3/3通过，源像素保持。修正提交c46a91d，Actions42139132026进行中。此前33d7bdf四文件仅保留审计，已标记superseded/do_not_flash；此前“准备完成”的该候选结论不再适用。仍未烧录，等新产物完整验证。ActorCodex。


## 2026-11-06T08:55:34.316435+08:00 2.5.6最终软件准备接受：c46a91d（尚未烧录）

- ActorCodex；接受软件范围T1/T2与页面交付，实体写入/真机验收门禁保持等待用户。c46a91d修复状态黑底遮挡，取代旧33d7bdf；Actions42139132026 SUCCESS。
- 固件153项/148PASS/5预期上游workflow缺失skip，独立宽度3PASS；服务端78PASS、人设14、情绪65；Gemini显示复审/资源/服务端/HTML PASS；独立页面37PASS。
- 状态字形宽38/58/57px，72px黑底+28px高度，保护头顶爱心/问号；图像未重绘。24EAF/168帧/39注册5FPS200ms，10字形齐全，当前板无真实电量继续隐藏。
- 四文件已下载Mac/Windows项目outputs/2.5.6-completion/artifact-c46a91d，app2685056 B / SHA256 6dc2590c11529a7beea14a1f6bca381d3970208c65bf2d31af4554d31a3fd0f0；assets6192626 B / SHA256 fd7a3d38e7fc4fc26c1d32fbfce646caecb2dd3a6f912989047ec3d1cd283ea1，≤8MiB，flashargs版本2.5.6提交c46a91d。
- 正式服务95a9fff从git树部署，私密备份保留；除prompt外配置语义未变，匿名WSS1008拒绝，真实HTTP情绪及thinking工具续接通过。密钥/思考原文不入记录。
- 验收单文件acceptance/index.html直接解码最终资源，提供24表情、爱心/问号/怒气、自动/手动与三状态、暂停/逐帧；仅浏览器预览，不是液晶实拍。操作手册与latest-release.json同目录。
- 详情docs/review/2.5.6-final-display-review.md及项目evidence。后续文档提交不改变c46a91d构建身份；不另触发CI。本轮未烧录/未合并main/未发布OTA。旧2.5.5/96fada8配对回滚与私密全量快照保留。


## 2026-11-06T13:21:39.786866+08:00 DOC256-HASH-20261106 completed / Codex

- 用户指出报告正文漏同步已退回33d7bdf的app哈希。已复算Mac/Windows实际c46a91d：app SHA256 6dc2590c11529a7beea14a1f6bca381d3970208c65bf2d31af4554d31a3fd0f0，assets SHA256 fd7a3d38e7fc4fc26c1d32fbfce646caecb2dd3a6f912989047ec3d1cd283ea1。当前报告正文只使用c46a91d/Actions42139132026；原报告原字节归档到docs/review/archive/2.5.6-gemini-review-33d7bdf-0cc0b62.md，历史审查响应不改。
- 当前页面仅移除初轮浏览器QA的过期app身份投影；24动画与渲染代码哈希相同。完整旧QA保留，当前manifest/校验文件/报告/页面均一致。Gemini3.8Flash文档限定复核PASS，Codex接受本次文档纠错。证据项目outputs/2.5.6-completion/evidence/doc-identity-correction-256.json与gemini-doc-identity-review-256.json。
- 项目内追加防重发规则：从实际产物与manifest生成当前校验信息，检查全文和展开证据，不只在末尾补更正。仅文档/输出元数据，不修改app/assets/固件/服务端，不触发CI，不烧录；用户审查与明确烧录确认仍等待。
