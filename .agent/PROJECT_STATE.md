# 项目状态（唯一事实源）

## 最新生效状态（2026-11-07 01:22，小马按 git / Actions / 串口日志 / 服务进程核实）

> 本节优先于本文件下方所有内容，也优先于其他状态页。下方旧内容只作历史，冲突时以本节为准。
> 其他状态页（`SYNC.md`、`STATUS.md`、Obsidian `50-小肥鱼/01-项目进度.md`、`00-目录清单.md`）只放指针，不另写一份。
> **改状态的人：动完立刻改本节**；涉及提交号、版本号、地址，先 `git show <commit>:<file>` 查实，不凭记忆。

| 项 | 当前值 | 依据 |
| :--- | :--- | :--- |
| 板上固件 | **2.5.7**，构建提交 `9c2c99d`（Actions `42255436477`）；2026-11-07 00:57 小马烧录，冷启动读回 `Current version: 2.5.7` 并进入 `listening` | `outputs/2.5.7-https/boot-log-2.5.7.log` |
| 固件现役分支 | `codex/2.5.7-https` = `9c2c99d`，本地与 fork 一致 | `git rev-parse`、`git push` |
| 上一版（回滚用） | 2.5.6 `c46a91d`（Actions `42139132026`），产物在 `outputs/2.5.6-completion/artifact-c46a91d`；档案 Obsidian `50-小肥鱼/03-2.5.6-交付档案.md` | `latest-release.json` |
| 产物 | 2.5.7 用 `outputs/2.5.7-https/artifact-9c2c99d/xiaozhi-lckfb-lichuang-dev/`：app `815be949…`、assets `fd7a3d38…`（与 2.5.6 同一份）。旧混版产物仍在 `.archive-20261106/`，**勿用** | `sha256sums.txt` |
| 回滚 | 2.5.6 `c46a91d` 成套 app + assets（`outputs/2.5.6-completion/artifact-c46a91d`）；2.5.5 / `96fada8` 的 16MiB 整片私密备份只作应急 | 2.5.6 验收报告 |
| 服务端运行 | `~/Services/xiaofeiyu/current` → `releases/server-8ce6677`（11-07 01:20 起），LaunchAgent `com.xiaofeiyu.server`；frpc 常驻（`com.xiaofeiyu.frpc`）。回滚：`current` 指回 `releases/server-d9105f3`（记忆仍读新目录前需先设 `XFY_MEMORY_DIR`，否则旧版会写回知识库）后 `launchctl kickstart -k gui/$(id -u)/com.xiaofeiyu.server`。**注意**：各版本共用的 `.venv` 实体在 `releases/server-fbf654b/` 里，该目录不能删 | `readlink`、`launchctl list` |
| 服务端源码 | `runtime/xiaozhi-esp32-server`，分支 `codex/2.5.6-emotion`，HEAD = 部署 `8ce6677`。`origin` 是官方上游，推送地址已设为 `DISABLED`（只拉不推） | `git log` |
| 运行时记忆 | 独立 Obsidian 仓库 `~/CodexWorkspace/ObsidianVaults/小肥鱼记忆库`（`~/Services/xiaofeiyu/state/memory` 是指向它的链接）（记忆卡、`02-事件/`、`99-归档/`、提炼状态），11-06 从知识库 `50-小肥鱼/` 迁出；`XFY_MEMORY_DIR` 可覆盖；事件流留 3 个月明文，更早压缩到 `99-归档/事件/`。知识库 `50-小肥鱼/` 只放项目文档 | `memory_obsidian.py` |
| 发布构建 | 一律用 `~/Services/xiaofeiyu/tools/build_release.sh <提交>`（自带自检）。11-06 23:33 手工构建把 `models` 链成了 `models/models`，声纹和 ASR 模型找不到，板子只显示聆听不答复，23:37 已修 | — |
| OTA 地址 | 固件默认 `https://47.117.142.184/xiaozhi/ota/`（2.5.5 起就是 https） | `main/Kconfig.projbuild` |
| 待实施 | `.agent/SPEC-pending-changes.md`：S1–S3 已实施并部署（`1214895`/`34f8f97`）；F1–F3 审核结论为现阶段不需要（见该文件第五部分） | — |
| 已知问题 | 11-06 日志里的三项已修并部署：记忆卡裁剪丢数据（S1–S3）、豆包 TTS 打断后 `StartSession failed`（`1ae1dcc`）、联网搜索 401 占位 Key（`658c737`）——**待真机对话复核**。仍待：人设废话多（待给标准）；2.5.6 的 9 项真机验收清单见交付档案第七节（2.5.7 已烧，验收对象改为 2.5.7）；服务端一次性告警 `Server sample rate 16000 does not match device output 24000`（重采样，非本版引入） | 服务端日志 11-06 / 11-07 冷启动 |
| 检索/提示词修复 | 11-07 01:20 部署（`8fd5ab7` + `8ce6677`）：① `search_notes` 把 `PROJECT_STATE.md` 列入语料并给 6 倍权重、片段固定取首节，历史日志不再盖过当前状态；② OTA 上报的固件版本落在 `state/data/device_versions.json`，注入提示词为「【设备自报固件版本】」，问版本时以此为准。成因：小肥鱼把版本答成 2.5.6，因为它只查知识库（`50-小肥鱼/` 被排除、`runtime/` 不在语料），命中了 11-06 的旧交接文档 | 服务端日志 01:00:26、01:20:49（提示词 8109 字） |
| 证书到期 | VPS 443 = Let's Encrypt IP 短期证书（`preferred_profile=shortlived`，7 天），本次 `notAfter 2026-11-12 04:09 UTC`。**自动续期已核实可用**（11-07 00:45 小马，SSH 查 VPS）：systemd `xiaofeiyu-cert-renew.timer` active+enabled，每 6 小时一次，最近 5 次（11-06 00:01/06:25/12:25/18:04、11-07 00:11）均 Finished；`certbot renew --dry-run` **全部成功**；webroot `/var/lib/xiaofeiyu/acme`，nginx 80 在听。certbot 5.9.0 装在 `/opt/xiaofeiyu/certbot-venv/bin/`，**不在 PATH**（`which certbot` 查不到，容易误判为"没装"）。ARI 下次检查 11-07 05:07 UTC。**唯一残留确认**：11-10 起看一眼 `notBefore` 是否已更新 | `systemctl list-timers`、`certbot certificates`、`renew --dry-run` 11-07 00:45 |

> 任何 Agent 动手前先读这一页，动完立刻改这一页。
> 最后更新：2026-11-07 01:22（首节：服务端切 8ce6677，检索与版本注入修复上线）；以下历史各节最后更新 2026-11-05 17:35

---

## 一、当前基线

| 项 | 值 | 说明 |
| :--- | :--- | :--- |
| 工作分支 | `wip/2.5.4-baseline` | 唯一有效基线 |
| 内容基线提交 | `72690ca`（11-05 17:35） | 已推送；本文件自身的后续提交不改变内容基线 |
| 远端基线 | `fork/wip/2.5.4-baseline` = `72690ca` | 与本地一致 |
| 版本号 | `2.5.3` | 已被 `xiaozhi.bin` 占用，**下一版必须用 2.5.4** |
| 工作区 | 干净 | 48 个 eaf 已固化进 `72690ca` |
| 废弃分支 | `feat/emote-touch-battery`（`d26086a`） | 已删，仅存 tag `archive/emote-touch-battery-d26086a` |

## 二、产物状态（有混版，禁止直接烧）

| 文件 | 版本 | 时间 | 可用性 |
| :--- | :--- | :--- | :--- |
| `firmware_bin/xiaozhi.bin` | 2.5.3 | 11-05 02:04 | 仅 app，无新 assets |
| `firmware_bin/merged-binary.bin` | **2.5.2** | 11-03 20:05 | **旧版，不含表情，禁止烧** |
| `firmware_bin/expression_assets.bin` | 未知 | 11-05 14:07 | 与代码版本不对应 |

## 三、作业租约（同一时间只允许一个 Agent 改同一片区域）

| 区域 | 持有者 | 起始 | 到期 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| 固件代码 `main/` | Codex | 2026-11-05T17:44:26+08:00 | 2026-11-05T20:44:26+08:00 | 待审：T1–T4 已实现，提交后交叉审查 |
| 表情资源 `assets/` | — | — | — | **空闲，可认领** |
| 服务端 `xiaozhi-esp32-server/` | 小马 | 11-05 09:00 | 11-06 09:00 | 占用 |
| 部署/运维（frp、VPS） | 小马 | 11-05 16:00 | 11-06 16:00 | 占用 |

认领方式：改这张表 + 在提交信息里写 `[agent:<名字>]`。到期未续，视为放弃。

## 四、已知冲突（未解决）

1. **两套手势实现**：`d26086a`（20ms/300/700/60px，已废弃）vs 现役（40ms/500/1200/40px）。只保留现役，删分支。
2. **两份 eaf**：`assets/emoji_large/` 与 `assets/pufferfish/` 内容相同，各 5.4MB。打包只用前者。
3. **48 个 eaf 改动未提交**：随时可能被 `git checkout` 冲掉。
4. **服务端配置仍指内网**：`websocket` 与 `vision_explain` 都是 `192.168.*`，出门必挂。

## 五、变更记录

| 时间 | 谁 | 改了什么 |
| :--- | :--- | :--- |
| 11-05 17:35 | 小马 | 建立本文件，登记基线漂移与混版产物 |
| 11-05 17:37 | 小马 | 固化 52 项改动为 `72690ca` 并推送；删除废弃分支，留 tag；新增 `.agent/SYNC.md` 与 `scripts/agent_guard.sh` |

## 2.5.4 实施租约（Codex）

| 区域 | 持有者 | 起始 | 到期 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| .github/workflows/build-lckfb.yml、验证与 docs/review/2.5.4-impl.md | Codex | 2026-11-05T17:44:26+08:00 | 2026-11-05T20:44:26+08:00 | 待审：T5 与验证交付已实现 |

- 2026-11-05T17:44:26+08:00：用户明确授权 Codex 执行 T1→T5，接手编码职责；起点 c19b11d，分支 feat/2.5.4-ota-public。创建分支时共享基线已推进到 02b40e7（两次状态文档提交），按用户固定提交要求仍从 c19b11d 创建。服务端与 frp 区域不接手；T6 与资源不改。

- 2026-11-05T17:51:13+08:00：Codex 按 T1→T5 完成实现，94 项相关主机测试通过；全量发现测试有 6 个已记录的既有/环境错误。交付 docs/review/2.5.4-impl.md，等待同 HEAD 云端验证与交叉审查，未自批准发布。

- 2026-11-05T18:04:25+08:00：Codex 依据 docs/review/2.5.4-review-b4d6058-xiaoma.md 修订 M1→M3，仅删除 CI 自检步、从 CMake 提取清单版本、改为 printf 生成清单并检查 commit；验证后交回同一分支等待小马复审。编译权归小马，未触发新的 CI。现有协作提交保留。

## 用户授权交接：2.5.4 完整候选版本

- 2026-11-05T18:24:21+08:00：用户决定 T7 并入 2.5.4、压缩表情；将后续全部开发/测试/编译/准备职责交给 Codex，独立审查交给 Gemini。该明确指令覆盖此前“小马独占编译/配置/frp”及“GPT 不写代码”的历史限制。当前代码从 feat/2.5.4-ota-public@94ce20a 继续，不回退 T1–T5。
- 私密备份已创建（路径仅存本机 .git/codex-release-context.json）；配置未输出或提交，原始资源与旧混版固件均保留。

| 区域 | 持有者 | 起始 | 到期 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| 固件代码与测试 | Codex | 2026-11-05T18:24:21+08:00 | 2026-11-06T00:24:21+08:00 | 占用；Gemini 独立审查 |
| 表情编码与资源 | Codex | 2026-11-05T18:24:21+08:00 | 2026-11-06T00:24:21+08:00 | 占用；Gemini 独立审查 |
| 服务端配置与故障修复 | Codex | 2026-11-05T18:24:21+08:00 | 2026-11-06T00:24:21+08:00 | 占用；Gemini 独立审查 |
| 编译、部署准备与信息同步 | Codex | 2026-11-05T18:24:21+08:00 | 2026-11-06T00:24:21+08:00 | 占用；Gemini 独立审查 |

## 2026-11-05T19:50:56+0800 Codex / Gemini 候选验收交接

- 用户新增模式/状态显示已实现；真实Gemini3.8Flash对3672528返回PASS。报告docs/review/2.5.4-gemini-3.8-flash.md。构建/四文件/尺寸/校验、固定密钥、16MiB备份已核实。
- 旧“视觉只断固件/launchctl自动化必失败”结论已更正：修复搜索占位密钥、假电量、视觉测试绕过和token刷新；GUI launchctl可用，Desktop TCC需版本化运行副本。
- 后续提交仅证据/状态，production code remains3672528；最终同HEAD产物以项目outputs/2.5.4-final/latest-release.json绑定。租约已交付，无其他Agent并发修改。
- 不烧录、不合并main、不发布OTA。实机验收和P2网络加固保留。

## 2026-11-05T20:49:57+0800 用户授权安全加固与资源错误修复

- 用户要求Codex将安全保护全部开启，保留受保护的Mac控制；修复缺失状态资源的事件调用。新分支codex/2.5.5-security，从4a8964aaee1df6e4c1a77ec0c497a2dad200703a继续，未重写任何已有分支。独立审查仍为Gemini3.8Flash。
- 本轮固件、服务端安全、TLS运维与私密设备凭据准备由Codex占用；小马已有STATUS提交保留。设备串口读写等待用户确认移交，当前不碰串口。密钥只存私密配置，不进入固件源码/提交/日志。
- 设计与计划见docs/superpowers/specs/2026-11-05-security-clean-emote.md。原2.5.4产物与备份保留，禁止混用新旧manifest。


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


## 2026-11-06T07:53:31.797383+08:00 Codex接手2.5.6需求完善

- 用户要求下版补齐情绪图形联动、待机/聆听/说话状态、人设、200–210ms；最新明确无真实电量继续隐藏。
- Codex统一开发，Gemini3.8Flash只独立审查。固件8ccb432继续，不回退别人提交；服务端既有未提交dialogue补丁先保留整合。T1固件资源/显示，T2服务端情绪/工具，根任务独占版本、集成、云编译/运维和最终验收记录。
- 规格docs/superpowers/specs/2026-11-06-2.5.6-expression-completion.md。当前只准备，不烧录/merge/发布，最终仍等用户确认。


## 2026-11-06T08:36:58.538168+08:00 2.5.6软件准备完成，待用户验收页审查/最终烧录确认

- 固件33d7bdf / 分支codex/2.5.6-completion；服务端95a9fff。用户最近明确：无真实电量继续隐藏，200–210ms范围允许5FPS200ms；情绪符号指原画爱心/问号/怒气。
- 28px标签修复真实字体25px高度裁剪，状态空闲/聆听中/说话中；显式情绪与说话状态先后顺序均通过，下一轮清理。24套无损压缩保留原像素，非重绘声明。
- Gemini3.8Flash(Antigravity)三范围PASS；独立固件147PASS5预期skip/服务端78PASS/人设14/情绪65案例。最终资源包24套168帧官方C/Python/源manifest一致，10字形齐全。
- Actions42136258139 SUCCESS，四文件已在Mac+Windows项目outputs/2.5.6-completion/artifact-33d7bdf；应用2.5.6/2685056字节，资源6192626字节。latest-release.json为产物身份真值；后续文档HEAD不冒充编译SHA。
- 正式服务已切至版本化server-95a9fff，私密配置备份，固定鉴权/TLS/控制工具确认规则保留。真实模型3情绪+两工具+thinking续接通过，未把思考/密钥写进证据。
- 单文件验收页outputs/2.5.6-completion/acceptance/index.html与人类操作手册xiaofeiyu_2.5.6_acceptance.md已备；网页不是液晶实拍/声音验收。
- 本轮未烧录、未发布OTA、未合并main。旧96fada8配对app/assets及全量私密备份保留；等用户明确确认再写设备。板上最新已核实仍2.5.5。此条优先于本文件早期2.5.4/未加固/未轮换等历史状态。
- Actor Codex，证据docs/review/2.5.6-gemini-review.md、项目outputs/2.5.6-completion/evidence。历史提交33d7bdf/95a9fff由Codex集成；后续提交带agent标识，不改写已构建提交。


## 2026-11-06T00:40:33.216590+00:00 2.5.6验收页发现遮挡，暂停33d7bdf候选

- 原状态标签黑底宽150遮住问号/爱心部分像素；root实际解码像素证据outputs/2.5.6-completion/evidence/overlay-occlusion-red.json。T1重新running，缩窄到三个字形可容纳范围后复审重编；旧33d7bdf不烧录，保留审计。先前“软件准备完成”被本条取代，等待新候选。ActorCodex。


## 2026-11-06T08:55:34.316435+08:00 2.5.6最终软件准备接受：c46a91d（尚未烧录）

- ActorCodex；接受软件范围T1/T2与页面交付，实体写入/真机验收门禁保持等待用户。c46a91d修复状态黑底遮挡，取代旧33d7bdf；Actions42139132026 SUCCESS。
- 固件153项/148PASS/5预期上游workflow缺失skip，独立宽度3PASS；服务端78PASS、人设14、情绪65；Gemini显示复审/资源/服务端/HTML PASS；独立页面37PASS。
- 状态字形宽38/58/57px，72px黑底+28px高度，保护头顶爱心/问号；图像未重绘。24EAF/168帧/39注册5FPS200ms，10字形齐全，当前板无真实电量继续隐藏。
- 四文件已下载Mac/Windows项目outputs/2.5.6-completion/artifact-c46a91d，app2685056 B / SHA256 6dc2590c11529a7beea14a1f6bca381d3970208c65bf2d31af4554d31a3fd0f0；assets6192626 B / SHA256 fd7a3d38e7fc4fc26c1d32fbfce646caecb2dd3a6f912989047ec3d1cd283ea1，≤8MiB，flashargs版本2.5.6提交c46a91d。
- 正式服务95a9fff从git树部署，私密备份保留；除prompt外配置语义未变，匿名WSS1008拒绝，真实HTTP情绪及thinking工具续接通过。密钥/思考原文不入记录。
- 验收单文件acceptance/index.html直接解码最终资源，提供24表情、爱心/问号/怒气、自动/手动与三状态、暂停/逐帧；仅浏览器预览，不是液晶实拍。操作手册与latest-release.json同目录。
- 详情docs/review/2.5.6-final-display-review.md及项目evidence。后续文档提交不改变c46a91d构建身份；不另触发CI。本轮未烧录/未合并main/未发布OTA。旧2.5.5/96fada8配对回滚与私密全量快照保留。


## 2026-11-06T13:18:10.989134+08:00 DOC256-HASH-20261106 running / Codex

- 用户指出旧审查报告正文沿用退回候选哈希。实际Mac/Windows app均6dc2590c...fd0f0，构建c46a91d。当前报告改为最终manifest校验清单；旧报告原字节归档，页面移除初轮QA的旧app身份投影，原证据不变。范围仅docs/状态与项目outputs；固件/设备/运行服务不变。等待文档核验与Gemini限定复核，不编译不烧录。


## 2026-11-06T13:21:39.786866+08:00 DOC256-HASH-20261106 completed / Codex

- 用户指出报告正文漏同步已退回33d7bdf的app哈希。已复算Mac/Windows实际c46a91d：app SHA256 6dc2590c11529a7beea14a1f6bca381d3970208c65bf2d31af4554d31a3fd0f0，assets SHA256 fd7a3d38e7fc4fc26c1d32fbfce646caecb2dd3a6f912989047ec3d1cd283ea1。当前报告正文只使用c46a91d/Actions42139132026；原报告原字节归档到docs/review/archive/2.5.6-gemini-review-33d7bdf-0cc0b62.md，历史审查响应不改。
- 当前页面仅移除初轮浏览器QA的过期app身份投影；24动画与渲染代码哈希相同。完整旧QA保留，当前manifest/校验文件/报告/页面均一致。Gemini3.8Flash文档限定复核PASS，Codex接受本次文档纠错。证据项目outputs/2.5.6-completion/evidence/doc-identity-correction-256.json与gemini-doc-identity-review-256.json。
- 项目内追加防重发规则：从实际产物与manifest生成当前校验信息，检查全文和展开证据，不只在末尾补更正。仅文档/输出元数据，不修改app/assets/固件/服务端，不触发CI，不烧录；用户审查与明确烧录确认仍等待。


## 2026-11-06T14:48:06.941413+08:00 HTTPS257-R1R4 running / Codex

- 用户派工单R1–R4限定实施，基线47acde1，分支codex/2.5.7-https。R1当前Kconfig5已为HTTPS，保留正确值；R2明确bundle与IP SAN链、显式板级安全配置；R3升2.5.7；R4检查时钟路径并加可观测日志。仅交分支等待小马审查，不触发CI/编译/烧录，不改服务端、表情和许可证锚点。


## 2026-11-06T14:55:03.264624+08:00 HTTPS257-R1R4 ready_for_review / Codex

- 基线47acde1，分支codex/2.5.7-https。R1 HTTPS默认地址原已正确保留；R2查明78/esp-ml3073.7.6实际EspSsl::Connect挂esp_crt_bundle_attach，ESP-IDF6.1原生IP SAN校验开启，显式板级bundle/full与禁止skip验证；正常同IP/受信CA链续期无需重编。R3版本2.5.7。R4增加SNTP初始化、TLS时钟就绪、OTA开始日志并验证先后。
- 本地主机153run/148pass/5预期skip exit0，最新针对TLS测试4pass exit0，格式检查通过。真实2.5.7冷启动串口时间线、CI/四件套、板上版本/HTTPS成功均待用户侧编译/烧录验收，未冒充完成。NVS公网旧HTTP覆盖值仍优先，交小马检查该单键，不扩展迁移或写NVS。
- 交付docs/review/2.5.7-https-handoff.md与项目outputs/2.5.7-https；不改服务端/表情/许可证，不触发CI或固件编译、不烧录、不合并main，等待小马审查。
