import os
import shlex
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MCP_SERVER = ROOT / "main" / "mcp_server.cc"


def extract_function(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def compiler_command():
    configured = os.environ.get("CXX")
    candidates = [configured] if configured else ["c++", "g++", "clang++"]
    for candidate in candidates:
        parts = shlex.split(candidate)
        if parts and shutil.which(parts[0]):
            return parts
    return None


class CameraToolRegistrationTests(unittest.TestCase):
    def test_camera_tool_registration_matrix(self):
        compiler = compiler_command()
        if compiler is None:
            self.skipTest("no host C++ compiler is available")

        add_common_tools = extract_function(
            MCP_SERVER.read_text(encoding="utf-8"),
            "void McpServer::AddCommonTools()",
        )
        self.assertIn("#ifdef HAVE_LVGL", add_common_tools)
        self.assertIn('AddTool("self.camera.take_photo"', add_common_tools)

        driver = textwrap.dedent(
            r"""
            #include <cassert>
            #include <expected>
            #include <functional>
            #include <initializer_list>
            #include <iterator>
            #include <string>
            #include <type_traits>
            #include <utility>
            #include <variant>
            #include <vector>

            enum PropertyType { kPropertyTypeInteger, kPropertyTypeString };

            class Property {
             public:
              Property(const std::string&, PropertyType) {}
              Property(const std::string&, PropertyType, int, int) {}

              template <typename T>
              const T& value() const {
                static const T value{};
                return value;
              }
            };

            class PropertyList {
             public:
              PropertyList() = default;
              PropertyList(std::initializer_list<Property>) {}

              const Property& operator[](const std::string&) const {
                static const Property property("", kPropertyTypeString);
                return property;
              }
            };

            using ReturnValue = std::variant<bool, int, std::string>;
            using ToolResult = std::expected<ReturnValue, std::string>;

            class Camera {
             public:
              bool capture_result = true;
              std::expected<std::string, std::string> explain_result =
                  std::string("vision explanation");
              int capture_calls = 0;
              int explain_calls = 0;
              std::string last_question;

              bool Capture() {
                ++capture_calls;
                return capture_result;
              }

              std::expected<std::string, std::string> Explain(
                  const std::string& question) {
                ++explain_calls;
                last_question = question;
                return explain_result;
              }
            };

            class Backlight {
             public:
              void SetBrightness(unsigned char, bool) {}
            };

            class Theme {};

            class Display {
             public:
              Theme* GetTheme() { return &theme_; }
              void SetTheme(Theme*) {}

             private:
              Theme theme_;
            };

            class LvglThemeManager {
             public:
              static LvglThemeManager& GetInstance() {
                static LvglThemeManager manager;
                return manager;
              }

              Theme* GetTheme(const std::string&) { return &theme_; }

             private:
              Theme theme_;
            };
            class AudioCodec {
             public:
              void SetOutputVolume(int) {}
            };

            class Board {
             public:
              static Board& GetInstance() {
                static Board board;
                return board;
              }

              Backlight* GetBacklight() { return backlight_; }
              Display* GetDisplay() { return display_; }
              Camera* GetCamera() { return camera_; }
              ReturnValue GetDeviceStatusJson() { return true; }
              AudioCodec* GetAudioCodec() { return &audio_codec_; }

              Backlight* backlight_ = nullptr;
              Display* display_ = nullptr;
              Camera* camera_ = nullptr;
              AudioCodec audio_codec_;
            };

            class TaskPriorityReset {
             public:
              explicit TaskPriorityReset(int) {}
            };

            class McpServer {
             public:
              static McpServer& GetInstance() {
                static McpServer server;
                return server;
              }
              void AddCommonTools();

              std::vector<std::string> names;
              std::function<ToolResult(const PropertyList&)> camera_tool;

              template <typename Callback>
              void AddTool(const std::string& name, const std::string&,
                           const PropertyList&, Callback callback) {
                names.push_back(name);
                using Result = std::invoke_result_t<Callback, const PropertyList&>;
                if constexpr (std::is_same_v<Result, ToolResult>) {
                  if (name == "self.camera.take_photo") {
                    camera_tool = std::move(callback);
                  }
                } else {
                  (void)callback;
                }
              }

              std::vector<int> tools_;
            };

            __ADD_COMMON_TOOLS__

            static bool HasTool(const McpServer& server, const std::string& name) {
              for (const auto& candidate : server.names) {
                if (candidate == name) {
                  return true;
                }
              }
              return false;
            }

            int main(int argc, char** argv) {
              assert(argc == 2);
              const bool camera_present = std::string(argv[1]) == "camera";
              Camera camera;
              Backlight backlight;
              Display display;
              auto& board = Board::GetInstance();
              board.camera_ = camera_present ? &camera : nullptr;
              board.backlight_ = &backlight;
              board.display_ = &display;

              auto& server = McpServer::GetInstance();
              server.AddCommonTools();
              assert(HasTool(server, "self.get_device_status"));
              assert(HasTool(server, "self.audio_speaker.set_volume"));
              assert(HasTool(server, "self.screen.set_brightness"));
              assert(HasTool(server, "self.camera.take_photo") == camera_present);

            #ifdef HAVE_LVGL
              assert(HasTool(server, "self.screen.set_theme"));
            #else
              assert(!HasTool(server, "self.screen.set_theme"));
            #endif

              if (!camera_present) {
                assert(!server.camera_tool);
                return 0;
              }

              assert(server.camera_tool);
              PropertyList properties;
              camera.capture_result = false;
              auto result = server.camera_tool(properties);
              assert(!result);
              assert(result.error() == "Failed to capture photo");
              assert(camera.capture_calls == 1);
              assert(camera.explain_calls == 0);

              camera.capture_result = true;
              camera.explain_result = std::string("vision explanation");
              result = server.camera_tool(properties);
              assert(result);
              assert(std::get<std::string>(*result) == "vision explanation");
              assert(camera.capture_calls == 2);
              assert(camera.explain_calls == 1);

              camera.explain_result =
                  std::unexpected(std::string("vision failure"));
              result = server.camera_tool(properties);
              assert(!result);
              assert(result.error() == "vision failure");
              assert(camera.capture_calls == 3);
              assert(camera.explain_calls == 2);
              return 0;
            }
            """
        ).replace("__ADD_COMMON_TOOLS__", add_common_tools)

        with tempfile.TemporaryDirectory(prefix="xiaozhi-camera-") as temp_dir:
            executable = Path(temp_dir) / "camera_tools_test"
            for have_lvgl in (False, True):
                command = compiler + [
                    "-std=c++23",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-Wno-unused-parameter",
                    "-x",
                    "c++",
                    "-",
                    "-o",
                    str(executable),
                ]
                if have_lvgl:
                    command.insert(1, "-DHAVE_LVGL")
                subprocess.run(
                    command,
                    input=driver,
                    text=True,
                    check=True,
                    cwd=ROOT,
                )
                for camera_present in (False, True):
                    subprocess.run(
                        [str(executable), "camera" if camera_present else "null"],
                        check=True,
                        cwd=ROOT,
                    )


if __name__ == "__main__":
    unittest.main()
