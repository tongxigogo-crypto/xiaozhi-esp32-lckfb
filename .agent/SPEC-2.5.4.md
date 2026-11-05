# 2.5.4 固件改动规格（给编码 Agent）

> 版本：v1.0（2026-11-05 17:45）
> 基线：`wip/2.5.4-baseline` @ `db06b84`
> 产出：一份可直接照着写的改动清单，不需要猜

---

## 交付要求

> **编译权只有小马持有。** 实现方交付分支 + 自述文档即止，**不得自行触发 `build-lckfb.yml`，不得下载产物，不得把产物当成可烧版本**。编译在审查通过后由小马统一发起。2026-11-05 已发生过一次越界（Codex 在 17:52 自行触发，编译失败）。

| 项 | 要求 |
| :--- | :--- |
| 分支名 | `feat/2.5.4-ota-public` |
| 起点 | `db06b84`（不许换基线） |
| 提交格式 | `feat(ota): ... [agent:<你的名字>]` |
| 交付内容 | 分支 + 一份 `docs/review/2.5.4-impl.md`，写清每个任务的改动与自检输出 |
| 不做的事 | 不合并 main、不发版、不动已在跑的 frps/frpc |

---

## T1｜OTA 默认地址改公网

**文件**：`main/Kconfig.projbuild` 第 5 行

**现状**：
```c
default "http://192.168.0.104:8003/xiaozhi/ota/"
```

**改为**：
```c
default "http://47.117.142.184:8003/xiaozhi/ota/"
```

**约束**：只改 `default`，`help` 文本不动。

**验收**：编译后 `grep CONFIG_OTA_URL sdkconfig` 显示公网地址。

---

## T2｜修复 `EraseKey` 不落盘（前置修复）

**文件**：`main/settings.cc` 第 91–99 行

**现状**：
```cpp
void Settings::EraseKey(const std::string& key) {
    if (read_write_) {
        auto ret = nvs_erase_key(nvs_handle_, key.c_str());
        if (ret != ESP_ERR_NVS_NOT_FOUND) {
            ESP_ERROR_CHECK(ret);
        }
    } else {
        ESP_LOGW(TAG, "Namespace %s is not open for writing", ns_.c_str());
    }
}
```

**问题**：`nvs_erase_key` 后没有置 `dirty_`，析构函数（第 12–19 行）只在 `dirty_` 为真时 `nvs_commit`，所以擦除可能不落盘。

**改为**：在 `nvs_erase_key` 成功后加一行
```cpp
        dirty_ = true;
```

**影响面**：`main/application.cc:454` 的 `settings.EraseKey("download_url")` 也一并修好——那里现在擦完不落盘，会导致 assets 重复下载。

**约束**：`EraseAll` 不动（它走 `nvs_erase_all`，语义不同）。

**验收**：写 key → EraseKey → 重启 → `GetString` 为空。

---

## T3｜清理陈旧的 `ota_url`

**文件**：`main/ota.cc` 第 54–61 行（`Ota::GetCheckVersionUrl`）

**现状**：
```cpp
std::string Ota::GetCheckVersionUrl() {
    Settings settings("wifi", false);
    std::string url = settings.GetString("ota_url");
    if (url.empty()) {
        url = CONFIG_OTA_URL;
    }
    return url;
}
```

**问题**：NVS 里只要存过内网地址就永远优先于编译默认值，旧板子改了 T1 也不会生效。

**改为**：
```cpp
static bool IsLocalUrl(const std::string& url) {
    return url.find("192.168.") != std::string::npos ||
           url.find("://127.") != std::string::npos ||
           url.find("://localhost") != std::string::npos;
}

std::string Ota::GetCheckVersionUrl() {
    Settings settings("wifi", true);
    std::string url = settings.GetString("ota_url");
    if (!url.empty() && IsLocalUrl(url)) {
        ESP_LOGW(TAG, "Dropping stale local ota_url: %s", url.c_str());
        settings.EraseKey("ota_url");
        url.clear();
    }
    if (url.empty()) {
        url = CONFIG_OTA_URL;
    }
    ESP_LOGI(TAG, "OTA check url: %s", url.c_str());
    return url;
}
```

**约束**：
- 只判这三种内网/回环形态，不要扩大匹配（避免误杀正常域名）
- 不加开关、不加配置项
- 不改 OTA 协议与请求头

**验收**：NVS 存过 `http://192.168.0.104:8003/...` 的板子，启动日志出现
`Dropping stale local ota_url`，随后显示公网地址。

---

## T4｜版本号 2.5.4

**文件**：`CMakeLists.txt` 第 12 行
```cmake
set(PROJECT_VER "2.5.3")   →   set(PROJECT_VER "2.5.4")
```

**约束**：2.5.3 已被烧过一版，不能复用。

**验收**：编译日志 `App "xiaozhi" version: 2.5.4`。

---

## T5｜产物清单加烧录参数

**文件**：`.github/workflows/build-lckfb.yml`

**现状**：只上传 `xiaozhi.bin`、`expression_assets.bin`、`sha256sums.txt`。

**改为**：额外生成 `build/flash-args.txt` 一并上传，内容固定为：

```
app     : 0x20000  xiaozhi.bin
assets  : 0x800000 expression_assets.bin
boot    : 0x0      bootloader/bootloader.bin
table   : 0x8000   partition_table/partition-table.bin
ota_data: 0xd000   ota_data_initial.bin
version : 2.5.4
commit  : <git rev-parse --short HEAD>
```

**约束**：不要上传 `merged-binary.bin`（现在那份是 2.5.2，混版源头）。

**验收**：artifact 内 4 个文件，`flash-args.txt` 的 commit 与实际 HEAD 一致。

---

## T6｜表情资源去重（需老大点头后才做）

**现状**：`assets/pufferfish/` 与 `assets/emoji_large/` 内容相同，各 5.4MB。

**改法**：删 `pufferfish/`，只留 `emoji_large/`。

**前置**：确认 `main/CMakeLists.txt` 打包只用 `emoji_large`（`7f89a39` 已改过路径，需复核）。

**不做也行**，只是仓库多 5.4MB。

---

## 不在本次范围

| 项 | 原因 |
| :--- | :--- |
| 电量显示 | 等硬件方案拍板 |
| TLS / WSS | 需要证书与时间同步方案，单独一轮 |
| 公网鉴权 | 服务端侧，小马负责 |
| 表情体积压缩 | 素材侧，老大决定 |
| 双地址探测 | 已评估为不必要 |

---

## 自检清单（提交前贴到 PR 描述里）

```bash
git rev-parse --short HEAD
grep -n "CONFIG_OTA_URL" sdkconfig
grep -n "PROJECT_VER" CMakeLists.txt
grep -n "dirty_ = true" main/settings.cc
git diff --stat wip/2.5.4-baseline..HEAD
```

五项输出贴齐，缺一项我按"未完成"退回。
