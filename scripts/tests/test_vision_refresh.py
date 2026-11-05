import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = r"""
#include <cstdint>
#include <cstring>
#include <functional>
#include <iostream>
#include <map>
#include <string>
#include <utility>
struct cJSON {
    int type;
    std::string text;
    char* valuestring;
    int valueint;
    std::map<std::string, cJSON*> fields;
    explicit cJSON(int t, std::string s = "", int n = 0)
        : type(t), text(std::move(s)), valuestring(text.data()), valueint(n) {}
};
cJSON* object() { return new cJSON(1); }
cJSON* string(const char* v) { return new cJSON(2, v); }
cJSON* number(int n) { return new cJSON(3, "", n); }
cJSON* cJSON_GetObjectItem(const cJSON* o, const char* k) {
    if (!o) return nullptr;
    auto it = o->fields.find(k); return it == o->fields.end() ? nullptr : it->second;
}
bool cJSON_IsObject(const cJSON* v) { return v && v->type == 1; }
bool cJSON_IsString(const cJSON* v) { return v && v->type == 2; }
bool cJSON_IsNumber(const cJSON* v) { return v && v->type == 3; }
bool cJSON_IsBool(const cJSON* v) { return v && v->type == 4; }
#define TAG "fixture"
#define ESP_LOGE(...) ((void)0)
#define BOARD_NAME "fixture-board"
struct AppDescription { const char* version = "2.5.4"; };
const AppDescription* esp_app_get_description() { static AppDescription d; return &d; }
using ResponseSender = std::function<void(const std::string&)>;
class McpServer {
public:
    int updates = 0, responses = 0;
    const cJSON* last_capabilities = nullptr;
    std::string last_result;
    void ParseMessage(const cJSON*, ResponseSender);
    void ParseCapabilities(const cJSON* p) { ++updates; last_capabilities = p; }
    void ReplyResult(int, const std::string& s, const ResponseSender&) { ++responses; last_result = s; }
    void ReplyError(int, int, const std::string&, const ResponseSender&) { ++responses; }
    void GetToolsList(int, const std::string&, bool, const ResponseSender&) {}
    void DoToolCall(int, std::string, const cJSON*, ResponseSender) {}
};
"""
MAIN = r"""
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    std::string mode = argv[1];
    McpServer s;
    auto request = object();
    request->fields["jsonrpc"] = string("2.0");
    auto params = object();
    params->fields["vision"] = object();
    request->fields["params"] = params;
    if (mode == "refresh") {
        request->fields["method"] = string("notifications/vision/update");
        s.ParseMessage(request, {});
        if (s.updates != 1 || s.last_capabilities != params || s.responses != 0) {
            std::cerr << "refresh notification must update capabilities without id/reply\n"; return 1;
        }
    } else if (mode == "malformed") {
        request->fields["method"] = string("notifications/vision/update");
        request->fields["params"] = string("bad");
        s.ParseMessage(request, {});
        if (s.updates != 0 || s.responses != 0) return 1;
    } else if (mode == "unknown") {
        request->fields["method"] = string("notifications/unrelated");
        s.ParseMessage(request, {});
        if (s.updates != 0 || s.responses != 0) return 1;
    } else if (mode == "initialize") {
        request->fields["method"] = string("initialize");
        request->fields["id"] = number(1);
        s.ParseMessage(request, {});
        if (s.responses != 1 || s.last_result.find("\"tokenRefresh\":true") == std::string::npos) {
            std::cerr << "initialize must advertise vision token refresh\n"; return 1;
        }
    } else return 2;
    return 0;
}
"""


def extract_function(source, signature):
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for i in range(opening, len(source)):
        depth += (source[i] == "{") - (source[i] == "}")
        if depth == 0:
            return source[start:i + 1]
    raise ValueError("Unclosed function")


class VisionRefreshFirmwareTest(unittest.TestCase):
    def test_notification_and_capability_negotiation(self):
        compiler = shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")
        self.assertIsNotNone(compiler, "host C++ compiler required")
        production = extract_function((ROOT / "main/mcp_server.cc").read_text(),
                                      "void McpServer::ParseMessage(const cJSON*")
        with tempfile.TemporaryDirectory(prefix="xiaozhi-vision-refresh-") as tmp:
            source = Path(tmp) / "test.cc"
            source.write_text(HARNESS + "\n" + production + "\n" + MAIN)
            executable = Path(tmp) / "test"
            subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                            str(source), "-o", str(executable)], check=True)
            for case in ("refresh", "malformed", "unknown", "initialize"):
                with self.subTest(case=case):
                    result = subprocess.run([str(executable), case], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
