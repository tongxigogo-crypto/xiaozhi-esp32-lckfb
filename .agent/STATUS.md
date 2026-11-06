# 最新生效状态：2.5.4 完整候选（Codex / Gemini）

> 更新：2026-11-05T19:50:56+0800。此节优先于下方保留的历史清单。
> 开发与验证：Codex；独立代码审查：Gemini 3.8 Flash（Antigravity）。
> 工作分支：feat/2.5.4-ota-public，从用户固定起点 c19b11d 继续。

Gemini审查PASS的功能提交为3672528：T1–T5公网OTA、T7相机注册、能力协商的拍照前token刷新、24表情无损压缩与去重、左上角自动/手动和真实状态显示。无采样的电量隐藏，不推断USB/电池电源。报告见 docs/review/2.5.4-gemini-3.8-flash.md。

| 编译/烧录前条件 | 已核实证据 |
| --- | --- |
| 编译success | run42019686320 @3672528；后续证据/同步提交也构建同HEAD |
| artifact四文件 | app、expression_assets、sha256sums、flash-args已下载 |
| version/commit对应 | 2.5.4/3672528；app header chip9；两项SHA256匹配 |
| assets ≤8MiB | 5,654,752字节；余2,733,856；EAF载荷减23.02%，168帧完全等价 |
| 固定server.auth_key | 私密mode600配置生效；重启前签发token重启后仍有效 |
| 旧固件备份 | 实板16MiB整片读出并复核SHA256；私密保存，不上传NVS |
| T7决策 | 用户已决定并入，已实现 |
| 烧录策略 | 板上同分区布局、ota0生效；app@0x20000 + assets@0x800000，保留boot/table/otadata |

最终交付和后续同HEAD构建的精确SHA、run、哈希、路径统一看项目 outputs/2.5.4-final/latest-release.json。该manifest在下载校验后生成。文档自引用不能代替二进制来源。禁止使用旧firmware_bin/merged-binary.bin配套烧录。

服务端在本机分支 codex/2.5.4-server-readiness@fbf654b，未推向上游官方仓库。公网红图识别成功、非法认证401、三次真搜索成功，12项服务端回归通过。原未提交工作独立snapshot21d3573；模型未删除。运行在 ~/Services/xiaofeiyu/current，共享state/；LaunchAgent com.xiaofeiyu.server 已运行并实测重启，需用户登录。原frpc保留。开发源码仍在Desktop，通过版本化运行副本规避launchd的Desktop TCC限制。

主机132项：127PASS，5个只针对已删除上游多板workflow的测试预期skip。CI含触摸、Settings/OTA、camera、vision refresh、UI字体生命周期、EAF和增量资源依赖回归。中文26字形齐全；静态预览不等于实机。

烧录后验收：24表情帧率/堆、模式及状态、触摸四手势、真实拍照和超过1小时后的刷新、麦克风/扬声器/对话。未实际烧录、未合并main、未发布OTA。P2保留TLS/WSS、公网WS访问加固、VPS到期迁移。相机失败底层错误码属Gemini建议项，驱动支持后再做。

以下原文为历史快照，授权、负责人、数字及状态冲突时，以本节与最终manifest为准。

---

# 小肥鱼 · 项目进度与待办（Agent 清单）

> 版本：v1.0（2026-11-05 18:30）
> 维护：小马｜所有 Agent 开工前读这一页
> 配套：`SYNC.md`（协作规则）、`SPEC-2.5.4.md`（改动规格）、`REVIEW_PROTOCOL.md`（审查协议）

---

## 一、一句话现状

公网链路已打通并实测（VPS + frps + frpc 常驻），2.5.4 固件正在编译；**视觉断在固件没注册相机工具**，不是服务端问题；表情资源已入仓但逼近 assets 分区上限。

---

## 二、已完成

### 2.1 网络与部署

| 项 | 状态 | 关键值 |
| :--- | :--- | :--- |
| 阿里云轻量（试用 1 个月） | ✅ | `47.117.142.184`，上海，2 核 1G，Ubuntu 24.04 |
| frps | ✅ | v0.61.0，systemd active，监听 7000 |
| frpc | ✅ | LaunchAgent `com.xiaofeiyu.frpc`，keepalive 实测有效 |
| 公网 OTA | ✅ | `http://47.117.142.184:8003/xiaozhi/ota/` → 200，约 0.1s |
| 公网 WS | ✅ | `ws://47.117.142.184:8000/xiaozhi/v1/` → 200 |
| 服务器防火墙 | ✅ | 7000 / 8000 / 8003 已放行 |

### 2.2 服务端

| 项 | 状态 | 说明 |
| :--- | :--- | :--- |
| 语音链路（ASR/声纹/TTS/记忆/LLM） | ✅ | 已实测，板子能正常对话 |
| `websocket` 地址 | ✅ 已改公网 | 原 `192.168.0.104` |
| `vision_explain` 地址 | ✅ 已改公网 | 原 `192.168.0.104`；**OTA 固件下载地址由它拼出** |
| `server.auth_key` | ❌ **未配置** | 每次启动随机 UUID → token 全部失效 |

### 2.3 固件

| 项 | 状态 |
| :--- | :--- |
| 基线分支 | `wip/2.5.4-baseline` |
| 表情资源 | 24 个 eaf 已入仓，`emote.json` 登记，fps 12 |
| 触摸手势 | 已实现（40ms 轮询 / 双击 500ms / 长按 1200ms / 横滑 40px） |
| 电量接口 | 已写，板子无采样电路 → 永远不显示 |
| 2.5.4 改动（T1–T5 + T7 + 资源压缩） | **已烧录并验证**（20:50，板子 MAC `9c:13:9e:8a:c7:74`） |
| 板上版本 | **2.5.4**（读回 app 描述符确认） |
| 版本号 | 2.5.4（2.5.3 已被烧过一版） |

### 2.4 协作机制

| 文件 | 作用 |
| :--- | :--- |
| `.agent/PROJECT_STATE.md` | 基线 + 作业租约 + 冲突登记 |
| `.agent/SYNC.md` | 给其他 Agent 的一页说明 |
| `.agent/REVIEW_PROTOCOL.md` | 审查前置与三档格式 |
| `.agent/SPEC-2.5.4.md` | T1–T6 规格，含“编译权归小马” |
| `scripts/agent_guard.sh` | 开工体检，dirty 不为 0 直接拦 |

---

## 三、需求清单（要做什么）

### P0 · 编译烧录前必须完成

> **已全部完成（2026-11-05 20:50）**。烧录记录见 `30-硬件资料/2.5.4-烧录记录-2026-11-05.md`。

| # | 事项 | 归属 | 卡点 |
| :-: | :--- | :--- | :--- |
| 1 | 编译成功且产物完整（app + assets + sha256 + flash-args） | 小马 | 进行中 |
| 2 | 配置固定 `server.auth_key` 并重启服务端 | 小马 | 否则烧完 token 仍会随机失效 |
| 3 | 决定 T7（相机工具未注册）是否并入 2.5.4 | 老大 | 并入则要重编一次 |
| 4 | 备份当前可用固件与 assets（回滚用） | 小马 | 未做 |
| 5 | 确认烧录参数（app `0x20000`，assets `0x800000`，16MB flash） | 小马 | 产物出来即可核对 |
| 6 | 表情资源去重（`pufferfish/` 5.4MB 重复） | 老大定 | 不阻塞烧录 |

### P1 · 影响出门体验

| # | 事项 | 归属 | 现状 |
| :-: | :--- | :--- | :--- |
| 7 | **T7 相机工具未注册**（视觉根因） | 编码 Agent | 已定位：设备只上报 5 个工具，无 `self.camera.take_photo` |
| 8 | 视觉 token 1 小时过期 | 编码 Agent | `auth.py:85` 硬编码，长连接超 1 小时静默失败 |
| 9 | 搜索进程内 401 | 待查 | 端点实测 200，但服务端进程内报 401，原因未闭环 |
| 10 | 表情体积（5.4MB，逼近 8MB 上限） | 老大 | 未压 |

### P2 · 后续

| # | 事项 | 说明 |
| :-: | :--- | :--- |
| 11 | 电量硬件方案 | 不做 / I2C 电量计 / 电池 + ADC，未拍板 |
| 12 | A5 控制电脑、A7 联网搜索 | 服务端能力，一直未落地 |
| 13 | TLS / WSS | 需要证书 + 时间同步，单独一轮 |
| 14 | 公网鉴权加固 | 白名单可绕过 token，公网暴露后有风险 |
| 15 | 试用机到期迁移 | 1 个月后，改 frpc `serverAddr` + 重装 frps |

---

## 四、编译烧录前的硬条件（逐条打勾才算完）

- [ ] 编译 run 结论为 success
- [ ] artifact 内有 4 个文件：`xiaozhi.bin`、`expression_assets.bin`、`sha256sums.txt`、`flash-args.txt`
- [ ] `flash-args.txt` 的 version = 2.5.4，commit = 本次 HEAD
- [ ] `expression_assets.bin` ≤ 8388608 字节（当前 6.6MB）
- [ ] `server.auth_key` 已固定并生效（重启后 token 不复位）
- [ ] 旧固件已备份（方便回滚）
- [ ] T7 是否并入已拍板
- [ ] 烧录用 `merged` 或“app + assets 分开写”，二者选一，不得只写 app

---

## 五、已知坑

1. **assets 分区不在 OTA 覆盖范围**。改资源必须单独写 `0x800000`，只 OTA app 会黑屏。
2. **`merged-binary.bin` 是 2.5.2 旧包**，与 2.5.3/2.5.4 的 app 混版，不能成套使用。
3. **自动化环境调 launchctl 会报 I/O error**，配 LaunchAgent 必须让老大在系统终端执行。
4. **服务端每次重启换 auth_key**，未配置固定值前，板子每重启一次就要重新连一次。
5. **视觉接口有 JWT 鉴权**（Bearer + 设备绑定），不是裸接口。

---

## 六、待老大拍板

| # | 决策 | 影响 |
| :-: | :--- | :--- |
| 1 | T7 并入 2.5.4 还是留给 2.5.5 | 决定今晚是否再编一次 |
| 2 | 电量：不做 / I2C 电量计 / 电池 + ADC | 决定是否动硬件 |
| 3 | 表情体积压不压 | 决定是否重导素材 |

---

## 七、变更记录

| 时间 | 谁 | 变更 |
| :--- | :--- | :--- |
| 11-05 18:30 | 小马 | 首版：汇总进度、需求、编译前硬条件 |

---

## 八、2026-11-05 20:50 烧录结果

| 项 | 结果 |
| :--- | :--- |
| 固件版本 | 2.5.4（板上 app 描述符读回确认） |
| 烧录内容 | app `0x20000` 2,677,072 B ／ assets `0x800000` 5,654,752 B |
| 校验 | 写入自动校验 + verify-flash digest 全部匹配 |
| 运行 | 表情模式启动、语音链路 listening/speaking 正常、SetEmotion 生效 |
| 基线修复 | `wip/2.5.4-baseline` 重指到 `b4ae94e`（曾回退到 02b40e7，已修） |
| 已知缺陷 | 资源包缺 `icon_speaker` / `icon_mic` / `listen` 动画，状态图标不显示；不影响功能 |
| 未验证 | 触摸手势、手机热点出门、拍照识别、公网 OTA 下载 |


## 2026-11-05T23:08:56.417827+08:00 Codex 安全与人设实机进展（尚非最终烧录验收）

- 正式运行服务已切至 serverfbb40a0；paired_device强鉴权已开启，公网HTTPS/WSS已验。匿名/错token/错client1008；未知OTA403；已配对OTA不下发私钥。Mac控制仍须设备鉴权+原有二次确认。
- VPS8000/8003仅loopback；FRP强制TLS，Mac验证ISRG RootX1+公网IP SAN；NGINX/FRP/续期timer均active。续期hook会短暂重启FRP，待最终重连验收。
- 用户授权的NVS配置已完成：仅0x9000/16KiB，3个目标键，MAC/分区/逐字节回读/非目标逻辑键均核验，其他WiFi/UUID保留。未写app/assets。
- 实际2.5.4板经新WSS连入，进入listening、相机工具注册；新版本冷启动日期校验和屏幕/音频仍未实测。
- 人设三层已统一：主prompt、TTS场景/疲惫兜底、主动搭话。对老大暖心为主，偶尔欢迎的斗嘴；保留黄蓉机灵护短。六次真实LLM文字抽测符合方向；实体语音尚未试听。Gemini3.8Flash人设/安全/工具/显示/时钟/NVS均分模块PASS（具体覆盖见outputs）。
- 发现此前遗漏：资源表文件名字段16字节截断字体名；原生对象工厂不接受mode_label/state_label。正在做最后显示修正，需32字节新资源表+配套app，旧assets不得混烧。现有4e6dd01构建成功，但不能作为含该最后修正的最终包。
- 一项DeepSeek API密钥误入本次工具输出，未进GitHub；已告知用户，模型后台撤销换新仍待账号入口配合。不在此记录任何值。


## 2026-11-05T23:34:58.088230+08:00 最终软件交付（新应用尚未烧录）

- 96fada8 / Actions42053435215成功；四件套已下载与核验，149主机测试及64服务端测试、七模块Gemini复审PASS。详见docs/review/2.5.5-gemini-review.md。
- 字体表32字节及原生自定义标签修复完成，所有旧表情和字体payload保持一致；新app+assets必须配套。软件准备完成，实体UI/音频/冷启动/热点仍待验收。
- 正式服务fbb40a0、人设三层、强鉴权/HTTPS/WSS/FRP证书校验/后端回环已生效；只写过NVS，当前实机仍2.5.4并已通过新链路进入聆听。
- 当前2.5.4+新凭据16MiB私密快照成功读取，原始快照保留。DeepSeek密钥换新待用户账号配合，不记录值。
- 后续文档提交不改变96fada8生产树，不另触发编译。产物真实构建SHA始终96fada8；outputs/2.5.5-security/latest-release.json另记交付文档SHA。未发布/合并main。


## 2026-11-06T01:07:01.589001+08:00 DeepSeek连接凭据更新

- 用户已将新凭据保存在本机私密文件；已更新聊天和视觉两处source/live配置及匹配的启动环境，重启正式服务。未修改固件、NVS、生产源码或构建产物。
- 新聊天请求通过，正式公网视觉接口红色测试图识别通过；新凭据未出现在服务日志，未写入Git。
- 旧凭据仍获服务商HTTP200；未撤销，故本轮轮换尚未闭环。已请用户在服务商后台撤销旧凭据，保留新凭据，随后再次验证。
- 证据仅记录成功/失败与HTTP状态，不记录任何凭据值；项目outputs/2.5.5-security/deepseek-key-rotation-2026-11-06.json。


## 2026-11-06T01:09:13.142691+08:00 DeepSeek凭据轮换闭环

- 用户已撤销旧凭据，独立接口复验：旧凭据HTTP401，新凭据HTTP200，无凭据HTTP401。source/live聊天与视觉配置均确认使用新凭据。
- 新聊天请求与正式公网视觉识别此前已通过；正式服务运行。密钥值未输出、未入Git；固件、NVS和构建产物均未修改。
- 状态由“等待用户撤销旧凭据”更新为“已验证完成”；证据outputs/2.5.5-security/evidence/deepseek-key-revocation-2026-11-06.json，仅含状态码。


## 2026-11-06T01:31:05.788906+08:00 更正实机安装状态与显示范围

- 用户反馈已烧2.5.5。查阅小马对话读回版本记录后，本轮只读核实：active ota0/版本2.5.5；esptool verify-flash确认app@0x20000与assets@0x800000均完整匹配96fada8，非只烧app。本轮未执行任何flash写入。此记录取代此前“未烧录”的旧状态。
- 本轮启动日志：完整字体Foundfont；mode_label/state_label均Created custom object成功；进入listening，未见旧缺图标/缺字体错误。尚未肉眼确认实际屏幕像素效果。
- 范围澄清：2.5.5仅显示事件适配、字体名表宽度及状态标签创建/生命周期修复，没有更换EAF画面。210ms没有实现；emote.json的idle/listening/neutral仍12fps（约83.3ms/帧），分别在fps行60/66/150。不存在可交付的210ms改动提交。
- 证据outputs/2.5.5-security/evidence/device-paired-96fada8-verified.json与current-display-diagnosis-2026-11-06.json。新表情素材来源需先与Gemini制作记录对齐，避免多Agent并改。


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
