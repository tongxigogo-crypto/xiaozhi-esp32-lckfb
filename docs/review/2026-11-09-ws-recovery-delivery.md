# 小肥鱼 WebSocket 断线恢复候选交付

本轮按用户批准方案修复，独立 Reviewer 与独立 QA 分离。本次 ESP-IDF 构建与产物哈希核验已通过；软件候选完成，实机验收待用户批准。任何部署、重启、烧录、OTA 发布、合入 main 均未授权。

## 已证实与未证实

- 19:20:30 的 -76 表示网络接收失败；现有串口证据不能证明 TCP RST 的来源，不能据此认定固件或 FRP 是断线根因。
- nginx WebSocket 超时实际为 3600 秒，与“35 秒回收”猜测不符。
- 已确认固件存在连续聆听意图在异常断线后丢失恢复路径的问题。
- 本轮同时增强可观测性、保活和有限恢复；实际网络故障来源仍待后续抓包或新的安全断连日志辅助确认。

## 候选身份

| 部分 | 候选 | 状态 |
| --- | --- | --- |
| 固件编译源 | 986aabd4159a11d4d97ac7193467917d169355b3 | 云端构建成功，已核验 |
| 服务端源 | 241075e2e3db98ba20b6c265464fa7451c13c47a | 软件接受，已打包未启用 |
| 服务端待启用目录 | /Users/tong/Services/xiaofeiyu/releases/server-241075e | 不修改 current |
| 实际生产指针 | /Users/tong/Services/xiaofeiyu/releases/server-39f36a4 | 保持不变 |
| 现役固件 | 317748c / 2.5.8 | 本轮未烧录 |

构建：[Actions 42506218869](https://github.com/tongxigogo-crypto/xiaozhi-esp32-lckfb/actions/runs/42506218869)。后续审计文档提交不得冒充实际编译源提交。

## 变更边界

固件将连续聆听意图、有限重试策略、网络任务生命周期分开管理。auto/realtime 意外断线按 1/2/4/8/16 秒退避，最多五次；恢复只做连接和原模式 listen/start，不问候、不主动发言、不重放旧音频。manual、明确停止、升级和取代回合取消恢复。旧工作线程、回调、JSON 和 MQTT goodbye 不能关闭或污染新会话。

新增 connection_recovery.h/.cc 承担策略；Application 承担状态协调；Protocol/WebSocket/MQTT 承担带来源和代次的传输生命周期。保留共享 Protocol 的 120 秒业务空闲语义，Ping 不算业务消息。

服务端候选默认 Ping 间隔 15 秒、超时 20 秒，可配置或显式关闭，拒绝非法数值。断连日志使用固定字段，记录会话、时长、关闭码、关闭顺序和错误类型/数值，不记录任意关闭原因、异常全文、消息或凭据。清理失败路径也经过泄漏负向验证。

认证、TLS 验证、板型引脚、NVS 和表情资源保持原边界，本轮不包含其他工单功能扩展。

## 独立验证

- 固件 Reviewer R3：完整相关 diff、CI、真实 Application/MQTT 方法适配测试审查 PASS；专项 20/20，exit 0。
- 固件 QA：专项 20/20；全量主机 176 项，其中 152 PASS、24 SKIP、0 FAIL/ERROR，exit 0。专项被全量包含，不相加。
- 24 项跳过沿用基线：上游 workflow 缺失 5、CMake 缺失 1、NVS 生成器缺失 8、PIL 缺失 10。云端环境将运行相关依赖已安装的既定测试。
- 服务端 Reviewer R2 PASS；独立 QA 共 141 个检查计数项通过；实际清理故障探针无敏感标记泄漏且连接关闭一次。
- 主机适配测试不能代替 ESP-IDF 编译、实体音频或现场网络测试。

固件 QA 命令：

```sh
CXX=clang++ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_connection_recovery*.py' -v
CXX=clang++ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test*.py' -v
```

证据：/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/，其中 fw-r2-qa-summary.json、fw-r2-qa-new.log、fw-r2-qa-full.log 保留命令、时间、退出码、计数与哈希；独立审查见 .agent/REVIEW_REPORT.md。

## 用户批准部署/烧录后执行的实机验收

1. 启用候选服务前复核当前指针、私密配置备份和回退目录；不在报告内复制配置或密钥。
2. 核对实际候选 app/assets 哈希、板型和偏移；保留原配套产物与可恢复备份。版本仍为 2.5.8，以编译提交区分候选，不能只看版本号。
3. 冷启动观察 auto/realtime 连接与原模式恢复；连接正常时验证服务器 Ping 与客户端 Pong。
4. 在连续聆听中制造一次受控断线，验证有限退避、单一在途连接、恢复一次 listen/start，无旧录音/旧播报/问候。
5. 在退避、握手、说话过程中分别停止、转手动、切 AEC 或升级，验证取消和旧回调隔离；manual 不自行恢复。
6. 连续失败达到上限后停止重试；新主人操作仍能连接。Wi-Fi 断开再恢复不得阻塞界面/音频主任务。
7. 回归触摸短音效、音色、记忆、MCP 及现有权限；保留共享 120 秒业务空闲语义，不把心跳误判成业务活动。
8. 保存脱敏串口与服务端关闭事件时间线；若异常复现，再通过抓包判定故障侧，不能由 -76 推断 RST。
9. 任一关键项失败，停止扩大使用并按成套产物/原服务目录回退，不混用不同构建资源。

当前实机结果均为待验；软件 PASS 不代表实体测试完成。

## 构建与产物核验

- Actions 42506218869 成功，实际编译源 986aabd4159a11d4d97ac7193467917d169355b3；仅构建产物。
- app：2,713,184 B；SHA256 157305edd34df90a7cb1e1e7c8a720d11f44c7e3c11866c6a1da4f3ef16a3335。
- assets：6,192,626 B；SHA256 fd7a3d38e7fc4fc26c1d32fbfce646caecb2dd3a6f912989047ec3d1cd283ea1，与现役 317748c 一致。
- 实际锁定依赖 78/esp-ml307 3.7.6；构建源码 Ping handler 调用 SendControlFrame(0xA, ...)，自动 Pong 已有实际编译依赖源码证据，实体心跳待验。
- Mac 与 Windows 两端 app/assets 哈希一致；flash-args.txt 绑定 2.5.8/986aabd，app 0x20000、assets 0x800000。
- 产物：/Users/tong/Desktop/网页设计/机器人DIY/outputs/ws-recovery-20261109/artifact-986aabd/。
- 机器清单：同级 latest-release.json；完整云端日志 actions-42506218869.log。
- 本文后续审计提交只记录交付，不改变已编译源身份。


## 最终软件接受与包使用范围

- 独立产物 QA 41 项断言通过，exit 0；独立集成 Reviewer PASS。软件候选范围接受，实体结果继续待验。
- 本包仅含 app、assets 及元数据，不含 flash-args.txt 列出的 bootloader、partition-table、ota_data 镜像，因此不是完整冷刷包，不能照抄该文件做全量烧录。
- 用户批准后的本次设备升级应先核验现有板型/分区，再仅更新 app@0x20000；assets 与现役完全相同，可保留。不得擅自写 bootloader、分区表、OTA 数据或 NVS。
- 如需冷刷或全盘恢复，必须另外准备、核验完整同版镜像；本文不宣称该能力已交付。
- 原配套 317748c 应用/资源产物保留；服务端原 current 目标 server-39f36a4 保留。启用新版本仍需用户确认。
