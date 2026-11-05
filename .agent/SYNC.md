# 给其他 Agent 的同步说明

> 读这一页就够，不要再去猜基线。
> 生成时间：2026-11-05 17:36｜生成者：小马（WorkBuddy）

---

## 一、基线在哪

```
仓库  tongxigogo-crypto/xiaozhi-esp32-lckfb
分支  wip/2.5.4-baseline
HEAD  72690ca
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

| 事项 | 归属 | 状态 |
| :--- | :--- | :--- |
| OTA 地址改公网 + NVS 迁移 | 小马 | 待做 |
| 服务端 `vision_explain` / 鉴权 | 小马 | 待做 |
| frpc 常驻（LaunchAgent） | 小马 | 待做 |
| 表情体积压缩（220KB → 目标 140KB） | 待定 | 等决策 |
| 电量硬件方案 | 老大 | 等拍板 |
| 版本号改 2.5.4 + 一次编译 | 小马 | 阻塞于上两项 |

## 七、审查怎么做

见 `.agent/REVIEW_PROTOCOL.md`。核心一条：**只审 `72690ca` 这个提交，不审工作区。**

审查结论请落到 `docs/review/72690ca-<你的名字>.md`，格式：必须改 / 建议改 / 可忽略，每条带证据（文件:行 或 命令输出）。
