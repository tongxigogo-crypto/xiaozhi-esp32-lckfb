"""Compile production overlay methods against a deterministic emote fixture."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def method(source, name):
    start = source.index(name)
    start = source.rfind("\n", 0, start) + 1
    brace = source.index("{", start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]

class InteractionOverlayTests(unittest.TestCase):
    def test_real_methods_preserve_state_and_font_lifetime(self):
        source = (ROOT / "main/display/emote_display.cc").read_text()
        methods = [
            "EmoteDisplay::~EmoteDisplay", "void EmoteDisplay::RefreshBatteryOverlay",
            "void EmoteDisplay::RefreshInteractionOverlay", "void EmoteDisplay::SetInteractionMode",
            "void EmoteDisplay::SetStatus", "void EmoteDisplay::LoadAssets",
            "void EmoteDisplay::UnmountAssets", "void EmoteDisplay::SetEmotion",
        ]
        bodies = "\n".join(method(source, name) for name in methods)
        header = (ROOT / "main/display/emote_display.h").read_text()
        fields = header[header.index("    emote_handle_t emote_handle_"):header.index("\n};")]
        cpp = r"""
#include <cstdint>
#include <cassert>
#include <cstring>
#include <cstdio>
#include <string>
#include <mutex>
#include <vector>
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGE(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
#define ESP_OK 0
#define GFX_COLOR_HEX(x) (x)
using emote_handle_t = void*;
struct lv_font_t {};
struct gfx_obj_t { std::string text; bool visible=false; void* font=nullptr; };
gfx_obj_t mode, state, battery;
bool loaded=false, locked=false, mounted=true, font_missing=false, load_failure=false;
int font_live=0, font_freed=0;
std::vector<std::string> events;
namespace Lang { namespace Strings {
const char* LISTENING="聆听"; const char* STANDBY="待机";
const char* SPEAKING="说话"; const char* ERROR="错误";
}}
enum {EMOTE_MGR_EVT_LISTEN,EMOTE_MGR_EVT_IDLE,EMOTE_MGR_EVT_SPEAK,EMOTE_MGR_EVT_SET};
int emote_lock(void*) {assert(!locked);locked=true;return 0;}
void emote_unlock(void*) {assert(locked);locked=false;}
gfx_obj_t* emote_get_obj_by_name(void*, const char* name) {
 assert(locked);
 if(!loaded)return nullptr;
 if(!strcmp(name,"mode_label"))return &mode;
 if(!strcmp(name,"state_label"))return &state;
 if(!strcmp(name,"battery_label"))return &battery;
 return nullptr;
}
void gfx_label_set_text(gfx_obj_t* o,const char* s){assert(locked);o->text=s;}
void gfx_label_set_color(gfx_obj_t*,int){assert(locked);}
void gfx_label_set_opa(gfx_obj_t*,int){assert(locked);}
void gfx_obj_set_visible(gfx_obj_t* o,bool b){assert(locked);o->visible=b;}
void gfx_label_set_font(gfx_obj_t* o,void* f){assert(locked);o->font=f;}
int emote_set_event_msg(void*,int,const char*){return 0;}
int emote_set_anim_emoji(void*,const char*){return 0;}
int emote_get_asset_data_by_name(void*,const char* n,const uint8_t** data,size_t* len){
 assert(mounted);assert(!strcmp(n,"font_puhui_common_20_4.bin"));
 static uint8_t bytes[32];*data=bytes;*len=sizeof(bytes);
 return font_missing ? -1 : 0;
}
lv_font_t* gfx_font_lv_load_from_binary(uint8_t*){++font_live;return new lv_font_t;}
void gfx_font_lv_delete(lv_font_t* f){
 assert(!loaded);assert(font_live==1);--font_live;++font_freed;delete f;
 events.push_back("free");
}
int emote_load_assets(void*){assert(!loaded);loaded=true;mode={};state={};battery={};return load_failure ? -1 : 0;}
int emote_unload_assets(void*){loaded=false;events.push_back("unload");return 0;}
int emote_unmount_assets(void*){assert(!loaded);assert(font_live==0);mounted=false;events.push_back("unmount");return 0;}
void emote_deinit(void*){emote_unload_assets(nullptr);mounted=false;}
namespace emote {
class EmoteDisplay {
public:
 EmoteDisplay(){emote_handle_=this;}
 ~EmoteDisplay();
 void SetEmotion(const char*);
 void SetInteractionMode(bool);
 void SetStatus(const char*);
 void LoadAssets();
 void UnmountAssets();
private:
 void RefreshBatteryOverlay();
 void RefreshInteractionOverlay();
""" + fields + "\n};\n" + bodies + r"""
}
int main(){
 {
 emote::EmoteDisplay d;
 d.SetInteractionMode(false);d.SetStatus(Lang::Strings::LISTENING);
 assert(!loaded);d.LoadAssets();
 assert(mode.visible && mode.text=="手动");
 assert(state.visible && state.text=="聆听");
 assert(mode.font && state.font==mode.font && font_live==1);
 assert(!battery.visible && battery.text.empty());
 d.SetEmotion("happy");
 assert(state.text=="聆听" && mode.text=="手动");
 d.SetInteractionMode(true);d.SetStatus(Lang::Strings::STANDBY);
 assert(mode.text=="自动" && state.text=="待机");
 d.LoadAssets(); // unload old labels before releasing their font
 assert(font_live==1 && font_freed==1);
 assert(state.text=="待机" && mode.text=="自动");
 d.SetStatus(Lang::Strings::SPEAKING);assert(state.text=="说话");
 d.SetStatus(nullptr);assert(!state.visible && state.text.empty());
 d.UnmountAssets();assert(font_live==0);
 assert(events[events.size()-3]=="unload" && events[events.size()-2]=="free" && events.back()=="unmount");
 }
 assert(font_live==0);
 mounted=true;load_failure=true;
 {emote::EmoteDisplay d;d.LoadAssets();assert(loaded && font_live==0);
 load_failure=false;d.LoadAssets();assert(loaded && font_live==1);}
 assert(!loaded && font_live==0);
 mounted=true;font_missing=true;
 {emote::EmoteDisplay d;d.SetStatus("聆听");d.LoadAssets();
 assert(!mode.visible && !state.visible); // no missing Chinese glyphs or fake status
 }
}
"""
        compiler = shutil.which("c++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "overlay.cc"
            binary = Path(tmp) / "overlay"
            src.write_text(cpp)
            subprocess.run([compiler, "-std=c++17", "-pthread", str(src), "-o", str(binary)], check=True, capture_output=True, text=True)
            subprocess.run([str(binary)], check=True, capture_output=True, text=True)

    def test_layout_and_application_use_real_mode(self):
        layout = json.loads((ROOT / "main/boards/lckfb/szpi-esp32s3/assets/320_240/layout.json").read_text())
        labels = {item["name"]: item for item in layout}
        for name in ["mode_label", "state_label"]:
            self.assertEqual(labels[name]["align"], "GFX_ALIGN_TOP_LEFT")
            self.assertLessEqual(labels[name]["x"]+labels[name]["width"],160)
        self.assertLessEqual(labels["mode_label"]["y"]+labels["mode_label"]["height"],labels["state_label"]["y"])
        source = (ROOT / "main/application.cc").read_text()
        body = method(source, "void Application::SetListeningMode")
        self.assertIn("SetInteractionMode(mode != kListeningModeManualStop)",body)
        self.assertIn("SetInteractionMode(listening_mode_ != kListeningModeManualStop)",source)
        # No synthetic state: display gets exactly the status emitted by application.
        self.assertIn("display->SetStatus(Lang::Strings::LISTENING)",source)
        self.assertIn("display->SetStatus(Lang::Strings::STANDBY)",source)

if __name__ == "__main__":
    unittest.main()
