import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

NVS_HEADER = r"""
#pragma once
#include <cstddef>
#include <cstdint>
using nvs_handle_t = unsigned;
constexpr int ESP_OK = 0;
constexpr int ESP_ERR_NVS_NOT_FOUND = 0x1102;
constexpr int NVS_READWRITE = 1;
constexpr int NVS_READONLY = 0;
#define ESP_ERROR_CHECK(value) do { if ((value) != ESP_OK) std::abort(); } while (0)
int nvs_open(const char*, int, nvs_handle_t*);
int nvs_commit(nvs_handle_t);
void nvs_close(nvs_handle_t);
int nvs_get_str(nvs_handle_t, const char*, char*, size_t*);
int nvs_set_str(nvs_handle_t, const char*, const char*);
int nvs_get_i32(nvs_handle_t, const char*, int32_t*);
int nvs_set_i32(nvs_handle_t, const char*, int32_t);
int nvs_get_u8(nvs_handle_t, const char*, uint8_t*);
int nvs_set_u8(nvs_handle_t, const char*, uint8_t);
int nvs_erase_key(nvs_handle_t, const char*);
int nvs_erase_all(nvs_handle_t);
"""

HARNESS = r"""
#include <cassert>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <map>
#include <string>
#include "settings.h"
static std::map<std::string, std::string> durable, staged;
static int commits = 0;
int nvs_open(const char*, int, nvs_handle_t* h) { *h = 1; staged = durable; return ESP_OK; }
int nvs_commit(nvs_handle_t) { durable = staged; ++commits; return ESP_OK; }
void nvs_close(nvs_handle_t) { staged.clear(); }
int nvs_get_str(nvs_handle_t, const char* key, char* out, size_t* length) {
    auto it = staged.find(key);
    if (it == staged.end()) return ESP_ERR_NVS_NOT_FOUND;
    *length = it->second.size() + 1;
    if (out) std::memcpy(out, it->second.c_str(), *length);
    return ESP_OK;
}
int nvs_set_str(nvs_handle_t, const char* key, const char* value) {
    staged[key] = value; return ESP_OK;
}
int nvs_erase_key(nvs_handle_t, const char* key) {
    return staged.erase(key) ? ESP_OK : ESP_ERR_NVS_NOT_FOUND;
}
int nvs_get_i32(nvs_handle_t, const char*, int32_t*) { return ESP_ERR_NVS_NOT_FOUND; }
int nvs_set_i32(nvs_handle_t, const char*, int32_t) { return ESP_OK; }
int nvs_get_u8(nvs_handle_t, const char*, uint8_t*) { return ESP_ERR_NVS_NOT_FOUND; }
int nvs_set_u8(nvs_handle_t, const char*, uint8_t) { return ESP_OK; }
int nvs_erase_all(nvs_handle_t) { staged.clear(); return ESP_OK; }
class Ota { public: std::string GetCheckVersionUrl(); };
#define TAG "Ota"
#include "esp_log.h"
"""

MAIN = r"""
int main(int argc, char** argv) {
    assert(argc == 2);
    const std::string mode = argv[1];
    Ota ota;
    if (mode == "erase_existing") {
        { Settings s("wifi", true); s.SetString("ota_url", "old"); }
        { Settings s("wifi", true); s.EraseKey("ota_url"); }
        { Settings s("wifi", false); assert(s.GetString("ota_url").empty()); }
        assert(commits == 2);
    } else if (mode == "erase_missing") {
        { Settings s("wifi", true); s.EraseKey("ota_url"); }
        assert(commits == 0);
    } else if (mode == "read_only") {
        durable["ota_url"] = "keep";
        { Settings s("wifi", false); s.EraseKey("ota_url"); }
        assert(durable.at("ota_url") == "keep" && commits == 0);
    } else if (mode == "preserve_other_key") {
        durable = {{"ota_url", "old"}, {"ssid", "keep"}};
        { Settings s("wifi", true); s.EraseKey("ota_url"); }
        assert(durable.count("ota_url") == 0 && durable.at("ssid") == "keep" && commits == 1);
    } else if (mode == "migrate_local") {
        for (const char* url : {"http://192.168.0.104:8003/xiaozhi/ota/",
                               "http://127.0.0.1:8003/xiaozhi/ota/",
                               "http://localhost:8003/xiaozhi/ota/"}) {
            durable = {{"ota_url", url}, {"ssid", "keep"}};
            commits = 0;
            assert(ota.GetCheckVersionUrl() == CONFIG_OTA_URL);
            { Settings s("wifi", false); assert(s.GetString("ota_url").empty()); }
            assert(commits == 1 && durable.at("ssid") == "keep");
            assert(ota.GetCheckVersionUrl() == CONFIG_OTA_URL && commits == 1);
        }
    } else if (mode == "preserve_public") {
        durable["ota_url"] = "https://ota.example.com/xiaozhi/ota/";
        assert(ota.GetCheckVersionUrl() == durable.at("ota_url") && commits == 0);
    } else if (mode == "preserve_other_ranges") {
        for (const char* url : {"http://10.0.0.1/ota", "http://172.16.0.1/ota"}) {
            durable["ota_url"] = url;
            assert(ota.GetCheckVersionUrl() == url && commits == 0);
        }
    } else if (mode == "empty_default") {
        assert(ota.GetCheckVersionUrl() == CONFIG_OTA_URL && commits == 0);
    } else {
        return 2;
    }
    std::cout << mode << ": PASS\n";
}
"""


def production_function(source, signature):
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for i in range(opening, len(source)):
        depth += (source[i] == "{") - (source[i] == "}")
        if depth == 0:
            return source[start:i + 1]
    raise AssertionError("Unclosed production function: " + signature)


class SettingsOtaRunnerTest(unittest.TestCase):
    def test_settings_persistence_and_ota_migration(self):
        compiler = next((shutil.which(c) for c in
                         (os.environ.get("CXX", "c++"), "g++", "clang++")
                         if shutil.which(c)), None)
        self.assertIsNotNone(compiler, "host C++ compiler required")
        ota = (ROOT / "main/ota.cc").read_text()
        functions = "\n".join(production_function(ota, name) for name in
                              ("static bool IsLocalUrl(", "std::string Ota::GetCheckVersionUrl("))
        kconfig = (ROOT / "main/Kconfig.projbuild").read_text()
        default_url = re.search(r'config OTA_URL\s+string[^\n]*\s+default "([^"]+)"', kconfig).group(1)
        self.assertEqual(default_url, "https://47.117.142.184/xiaozhi/ota/")
        with tempfile.TemporaryDirectory(prefix="xiaozhi-settings-") as temp:
            folder = Path(temp)
            (folder / "nvs_flash.h").write_text(NVS_HEADER)
            (folder / "esp_log.h").write_text(
                "#pragma once\n#define ESP_LOGW(...) ((void)0)\n#define ESP_LOGI(...) ((void)0)\n")
            fixture = folder / "test.cc"
            fixture.write_text(HARNESS + '\n#define CONFIG_OTA_URL "' + default_url + '"\n'
                               + functions + "\n" + MAIN)
            executable = folder / "settings_ota_test"
            subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                            "-include", "cstdlib", "-I", str(folder), "-I", str(ROOT / "main"),
                            str(ROOT / "main/settings.cc"), str(fixture),
                            "-o", str(executable)], check=True)
            for case in ("erase_existing", "erase_missing", "read_only", "preserve_other_key",
                         "migrate_local", "preserve_public", "preserve_other_ranges", "empty_default"):
                with self.subTest(case=case):
                    subprocess.run([str(executable), case], check=True)


if __name__ == "__main__":
    unittest.main()
