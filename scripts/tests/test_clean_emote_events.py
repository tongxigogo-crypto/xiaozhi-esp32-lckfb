"""Event adapter regression: production setters with pinned emote 1.0.2 event effects.

Upstream emote_op.c looks up resources before testing widget existence:
LISTEN -> listen/icon_mic; SPEAK -> icon_speaker; SYS/SET -> icon_tips;
IDLE -> icon_battery_bg/icon_battery_charge and clock.
Source: expression1.0.2, commit5c290a6304a9d84dc410a20613f97c19d6ae95bc.
The fixture records those lookups so the old adapter fails on a clean layout.
"""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_interaction_overlay import method

ROOT = Path(__file__).resolve().parents[2]

class CleanEmoteEventsTests(unittest.TestCase):
    def test_clean_and_legacy_setters(self):
        source = (ROOT / "main/display/emote_display.cc").read_text()
        names = ["SetEmotion", "SetStatus", "SetChatMessage", "SetBatteryLevel", "ShowNotification"]
        if "void EmoteDisplay::SetEventMessage" in source:
            names.append("SetEventMessage")
        bodies = "\n".join(method(source, "void EmoteDisplay::"+name) for name in names)
        header = (ROOT / "main/display/emote_display.h").read_text()
        fields = header[header.index("    emote_handle_t emote_handle_"):header.index("\n};")]
        cpp = r"""
#include <cassert>
#include <algorithm>
#include <cstring>
#include <cstdio>
#include <string>
#include <mutex>
#include <vector>
#define ESP_LOGI(...) ((void)0)
#define ESP_OK 0
using emote_handle_t=void*;
struct lv_font_t{};
struct gfx_obj_t { std::string text; bool visible=false; };
gfx_obj_t icon, listen, toast;
bool legacy=false, with_toast=false, locked=false;
std::vector<std::string> lookups, events, animations;
namespace Lang { namespace Strings {
const char* LISTENING="聆听中..."; const char* STANDBY="待命";
const char* SPEAKING="说话中..."; const char* ERROR="错误";
}}
const char* EMOTE_MGR_EVT_LISTEN="listen";
const char* EMOTE_MGR_EVT_IDLE="idle";
const char* EMOTE_MGR_EVT_SPEAK="speak";
const char* EMOTE_MGR_EVT_SET="set";
const char* EMOTE_MGR_EVT_SYS="sys";
const char* EMOTE_MGR_EVT_BAT="bat";
int emote_lock(void*){assert(!locked);locked=true;return 0;}
void emote_unlock(void*){assert(locked);locked=false;}
gfx_obj_t* emote_get_obj_by_name(void*,const char* n){
 assert(locked);
 if(!strcmp(n,"status_icon"))return legacy ? &icon : nullptr;
 if(!strcmp(n,"listen_anim"))return legacy ? &listen : nullptr;
 if(!strcmp(n,"toast_label"))return with_toast ? &toast : nullptr;
 return nullptr;
}
void gfx_label_set_text(gfx_obj_t* o,const char* s){assert(locked);o->text=s?s:"";}
void gfx_obj_set_visible(gfx_obj_t* o,bool b){assert(locked);o->visible=b;}
int emote_set_anim_emoji(void*,const char* n){animations.push_back(n);return 0;}
int emote_set_event_msg(void*,const char* ev,const char* msg){
 assert(!locked);events.push_back(ev);
 if(!strcmp(ev,"listen")){lookups.push_back("listen");lookups.push_back("icon_mic");}
 if(!strcmp(ev,"speak"))lookups.push_back("icon_speaker");
 if(!strcmp(ev,"sys")||!strcmp(ev,"set"))lookups.push_back("icon_tips");
 if(!strcmp(ev,"idle")){lookups.push_back("icon_battery_bg");lookups.push_back("icon_battery_charge");}
 return 0;
}
namespace emote {
class EmoteDisplay {
public:
 EmoteDisplay(){emote_handle_=this;assets_loaded_=true;}
 void SetEmotion(const char*);
 void SetStatus(const char*);
 void SetChatMessage(const char*,const char*);
 void SetBatteryLevel(int,bool);
 void ShowNotification(const char*,int=3000);
private:
 void SetEventMessage(const char*,const char*);
 void RefreshBatteryOverlay(){}
 void RefreshInteractionOverlay(){}
""" + fields + "\n};\n" + bodies + r"""
}
int main(){
 emote::EmoteDisplay d;
 d.SetStatus(Lang::Strings::LISTENING);
 assert(lookups.empty()); assert(animations.back()=="listening");
 d.SetEmotion("neutral");assert(animations.back()=="listening");
 d.SetEmotion("happy");assert(animations.back()=="happy");
 d.SetStatus(Lang::Strings::SPEAKING);assert(animations.back()=="speaking");
 d.SetChatMessage("assistant","你好");
 d.SetChatMessage("system","xiaozhi.me\nhello");
 d.ShowNotification("网络错误");
 d.SetStatus(Lang::Strings::ERROR);
 d.SetBatteryLevel(-1,false);
 assert(lookups.empty());
 d.SetBatteryLevel(85,false);assert(lookups.empty());
 d.SetStatus(Lang::Strings::STANDBY);assert(animations.back()=="idle");
 assert(lookups.empty());
 // Optional existing toast remains usable without a legacy status icon.
 with_toast=true;
 d.ShowNotification("提示");assert(toast.visible && toast.text=="提示");
 d.SetChatMessage("assistant","回答");assert(toast.text=="回答");
 d.SetChatMessage(nullptr,"安全");assert(toast.text=="安全");
 // Legacy assets keep the component's event/icon behavior.
 legacy=true;events.clear();lookups.clear();
 d.SetStatus(Lang::Strings::LISTENING);
 d.SetStatus(Lang::Strings::SPEAKING);
 d.SetStatus(Lang::Strings::STANDBY);
 d.ShowNotification("提示");
 d.SetBatteryLevel(0,false);
 assert((events==std::vector<std::string>{"listen","speak","idle","sys","bat"}));
 assert(!lookups.empty());
}
"""
        compiler=shutil.which("c++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"events.cc";out=Path(tmp)/"events"
            src.write_text(cpp)
            result=subprocess.run([compiler,"-std=c++17","-pthread",str(src),"-o",str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_current_clean_layout_uses_registered_state_assets(self):
        base=ROOT/"main/boards/lckfb/szpi-esp32s3/assets/320_240"
        layout=json.loads((base/"layout.json").read_text())
        self.assertTrue({"status_icon","listen_anim"}.isdisjoint(item["name"] for item in layout))
        names={item["emote"] for item in json.loads((base/"emote.json").read_text())}
        self.assertTrue({"idle","listening","speaking"}.issubset(names))
