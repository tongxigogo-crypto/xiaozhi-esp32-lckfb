"""Compile production overlay methods against a deterministic emote fixture."""
import hashlib
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
            "EmoteDisplay::~EmoteDisplay", "void EmoteDisplay::SetBatteryLevel", "void EmoteDisplay::SetEventMessage", "void EmoteDisplay::RefreshBatteryOverlay",
            "void EmoteDisplay::RefreshInteractionOverlay", "void EmoteDisplay::SetInteractionMode",
            "void EmoteDisplay::SetStatus", "void EmoteDisplay::LoadAssets",
            "void EmoteDisplay::UnmountAssets", "void EmoteDisplay::SetEmotion",
            "bool EmoteDisplay::CreateInteractionLabels", "bool EmoteDisplay::InsertAnimDialog", "void EmoteDisplay::ShowNotification",
        ]
        bodies = "\n".join(method(source, name) for name in methods)
        header = (ROOT / "main/display/emote_display.h").read_text()
        fields = header[header.index("    emote_handle_t emote_handle_"):header.index("\n};")]
        fixture = ROOT / "scripts/tests/fixtures/esp_emote_gfx_render_3_0_5"
        render_source = (fixture / "gfx_render.c").read_bytes()
        self.assertEqual(hashlib.sha256(render_source).hexdigest(),
                         json.loads((fixture / "PROVENANCE.json").read_text())["sha256"])
        renderer = method(render_source.decode(), "void gfx_render_draw_child_objects")
        cpp = r"""
#include <cstdint>
#include <cassert>
#include <cstring>
#include <cstdio>
#include <cinttypes>
#include <string>
#include <mutex>
#include <vector>
void check_arg(const char* p){assert(p);}
template<typename T>void check_arg(T){}
template<typename... Args>void checked_log(const char*,const char*,Args... args){(check_arg(args),...);}
#define TAG "test"
#define ESP_LOGI(...) checked_log(__VA_ARGS__)
#define ESP_LOGE(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
#define ESP_OK 0
#define GFX_COLOR_HEX(x) (x)
using emote_handle_t = void*;
struct lv_font_t { int line_height=25; };
struct gfx_draw_ctx_t { mutable int pixels[2]; };
struct gfx_obj_t;
struct gfx_vfunc { void (*draw)(gfx_obj_t*,const gfx_draw_ctx_t*)=nullptr; };
struct gfx_state { bool is_visible=true; };
struct gfx_obj_t { gfx_vfunc vfunc; gfx_state state;  std::string text; bool visible=false; void* font=nullptr; int x=0,y=0,w=0,h=0,color=0,opa=0,bg=0; bool bg_enabled=false,dirty=false; };
gfx_obj_t mode, state, battery, eye, dialog;
struct gfx_obj_child_t { void* src; gfx_obj_child_t* next; };
struct gfx_disp_t { gfx_obj_child_t* child_list=nullptr; };
gfx_disp_t display;
gfx_obj_child_t nodes[4];
int node_count=0;
void append(gfx_obj_t* o){nodes[node_count]={o,nullptr};if(node_count)nodes[node_count-1].next=&nodes[node_count];else display.child_list=&nodes[0];++node_count;}
void paint_animation(gfx_obj_t*,const gfx_draw_ctx_t* c){c->pixels[0]=c->pixels[1]=0x38BDF8;}
void paint_overlay(gfx_obj_t*,const gfx_draw_ctx_t*);
""" + renderer + r"""

bool loaded=false, locked=false, mounted=true, font_missing=false, load_failure=false, labels_created=false;
int font_live=0, font_freed=0; bool create_failure=false;
std::vector<std::string> events;
std::string animation;
namespace Lang { namespace Strings {
const char* LISTENING="聆听"; const char* STANDBY="待机";
const char* SPEAKING="说话"; const char* ERROR="错误";
}}
const char* EMOTE_MGR_EVT_LISTEN="listen"; const char* EMOTE_MGR_EVT_IDLE="idle";
const char* EMOTE_MGR_EVT_SPEAK="speak"; const char* EMOTE_MGR_EVT_SET="set"; const char* EMOTE_MGR_EVT_BAT="bat"; const char* EMOTE_MGR_EVT_SYS="sys";
int emote_lock(void*) {assert(!locked);locked=true;return 0;}
void emote_unlock(void*) {assert(locked);locked=false;}
gfx_obj_t* emote_get_obj_by_name(void*, const char* name) {
 assert(locked);
 if(!loaded)return nullptr;
 if(!strcmp(name,"mode_label"))return labels_created ? &mode : nullptr;
 if(!strcmp(name,"state_label"))return labels_created ? &state : nullptr;
 if(!strcmp(name,"battery_label"))return &battery;
 return nullptr;
}
enum {GFX_ALIGN_TOP_LEFT,GFX_TEXT_ALIGN_LEFT,GFX_LABEL_LONG_CLIP};
gfx_obj_t* emote_create_obj_by_type(void*,const char* type,const char* name){
 assert(loaded && !locked && !strcmp(type,"label"));
 if(create_failure && !strcmp(name,"state_label"))return nullptr;
 labels_created=true;
 auto obj=!strcmp(name,"mode_label") ? &mode : &state;
 obj->vfunc.draw=paint_overlay;append(obj);return obj;
}
void gfx_obj_align(gfx_obj_t* o,int,int x,int y){assert(locked);o->x=x;o->y=y;}
void gfx_obj_set_size(gfx_obj_t* o,int w,int h){assert(locked);o->w=w;o->h=h;}
void gfx_label_set_text_align(gfx_obj_t*,int){assert(locked);}
void gfx_label_set_long_mode(gfx_obj_t*,int){assert(locked);}
void gfx_label_set_text(gfx_obj_t* o,const char* s){assert(locked);o->text=s;}
void gfx_label_set_color(gfx_obj_t* o,int c){assert(locked);o->color=c;}
void gfx_label_set_bg_color(gfx_obj_t* o,int c){assert(locked);o->bg=c;}
void gfx_label_set_bg_enable(gfx_obj_t* o,bool b){assert(locked);o->bg_enabled=b;o->dirty=true;}
void gfx_label_set_opa(gfx_obj_t* o,int a){assert(locked);o->opa=a;}
void gfx_obj_set_visible(gfx_obj_t* o,bool b){assert(locked);o->visible=b;o->state.is_visible=b;o->dirty=true;}
void gfx_label_set_font(gfx_obj_t* o,void* f){assert(locked);o->font=f;}
int emote_set_event_msg(void*,const char*,const char*){return 0;}
int emote_set_anim_emoji(void*,const char* name){assert(loaded);if(!strcmp(name,"missing"))return -1;animation=name;return 0;}
bool emote_insert_anim_dialog(void*,const char*,uint32_t){assert(loaded);return true;}
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
int emote_load_assets(void*){assert(!loaded);loaded=true;labels_created=false;mode={};state={};battery={};node_count=0;eye={};dialog={};eye.vfunc.draw=dialog.vfunc.draw=paint_animation;append(&eye);append(&dialog);return load_failure ? -1 : 0;}
int emote_unload_assets(void*){loaded=false;labels_created=false;events.push_back("unload");return 0;}
int emote_unmount_assets(void*){assert(!loaded);assert(font_live==0);mounted=false;events.push_back("unmount");return 0;}
void emote_deinit(void*){emote_unload_assets(nullptr);mounted=false;}
namespace emote {
class EmoteDisplay {
public:
 EmoteDisplay(){emote_handle_=this;}
 ~EmoteDisplay();
 void SetEmotion(const char*);
 void SetBatteryLevel(int,bool);
 bool InsertAnimDialog(const char*,uint32_t);
 void ShowNotification(const char*,int=3000);
 void SetInteractionMode(bool);
 void SetStatus(const char*);
 void LoadAssets();
 void UnmountAssets();
private:
 bool CreateInteractionLabels();
 void SetEventMessage(const char*, const char*);
 void RefreshBatteryOverlay();
 void RefreshInteractionOverlay();
""" + fields + "\n};\n" + bodies + r"""
}
// Gfx3.0.5 appends children and redraws ALL visible children in list order,
// including clean labels when an animation invalidates the covered rectangle.
// Its line count is clamped to at least one, then a line-height bounds check
// stops painting when the real 25px font cannot fit a 24px widget.
int paint_label(gfx_obj_t& o,int under){
 if(!o.visible)return under;
 int pixel=o.bg_enabled ? o.bg : under;
 int line_height=static_cast<lv_font_t*>(o.font)->line_height;
 int lines=o.h/(line_height+2);
 if(lines<=0)lines=1; // official gfx_draw_label.c:986-987
 int current_y=0;
 if(current_y+line_height>o.h)return pixel; // official :993-994
 return lines>0 && !o.text.empty() ? o.color : pixel;
}
void paint_overlay(gfx_obj_t* o,const gfx_draw_ctx_t* c){
 int index=o==&mode ? 0 : 1;c->pixels[index]=paint_label(*o,c->pixels[index]);
}
void assert_frame(){
 assert(mode.dirty || state.dirty);
 int saved_height=mode.h;
 mode.h=24;assert(paint_label(mode,0)==0);
 mode.h=25;assert(paint_label(mode,0)==0xFFFFFF); // clamped first line fits
 mode.h=saved_height;
 for(int animation_color : {0x38BDF8,0x000000,0xFFFFFF}){
  gfx_draw_ctx_t ctx{{animation_color,animation_color}};
  gfx_render_draw_child_objects(&display,&ctx);
  assert(ctx.pixels[0]==0xFFFFFF && ctx.pixels[1]==0xFFFFFF);
  // eye_anim and emerg_dlg are created before custom labels.
  assert(paint_label(mode,animation_color)==0xFFFFFF);
  assert(paint_label(state,animation_color)==0xFFFFFF);
  assert(mode.bg_enabled && state.bg_enabled && mode.bg==0 && state.bg==0);
  assert(mode.opa==255 && state.opa==255);
 }
 mode.dirty=state.dirty=false;
 // Next animation-only invalidation still repaints clean overlays.
 gfx_draw_ctx_t ctx{{0,0}};gfx_render_draw_child_objects(&display,&ctx);
 assert(ctx.pixels[0]==0xFFFFFF && ctx.pixels[1]==0xFFFFFF);
 assert(paint_label(mode,0x38BDF8)==0xFFFFFF);
 assert(paint_label(state,0x38BDF8)==0xFFFFFF);
}
int main(){
 {
 emote::EmoteDisplay d;
 d.SetInteractionMode(false);d.SetStatus(Lang::Strings::LISTENING);
 assert(!loaded);d.LoadAssets();
 assert(mode.visible && mode.text=="手动");assert_frame();
 assert(mode.x==6 && mode.y==4 && mode.w==60 && mode.h>=27);
 assert(state.x==6 && state.y==34 && state.w==150 && state.h>=27);
 assert(state.visible && state.text=="聆听中");
 assert(mode.font && state.font==mode.font && font_live==1);
 assert(!battery.visible && battery.text.empty());
 d.SetBatteryLevel(75,false);assert(battery.visible && battery.text=="75%");
 d.SetBatteryLevel(-1,false);assert(!battery.visible && battery.text.empty());
 for(const char* emotion : {"happy","jealous","protect","curious","roast","sulk","listening"}){
 d.SetEmotion(emotion);
 assert(state.text=="聆听中" && mode.text=="手动");assert_frame();
 }
 d.SetEmotion("happy");
 assert(state.text=="聆听中" && mode.text=="手动");
 d.SetInteractionMode(true);d.SetStatus(Lang::Strings::STANDBY);
 assert(mode.text=="自动" && state.text=="空闲");assert_frame();
 d.LoadAssets(); // unload old labels before releasing their font
 assert(font_live==1 && font_freed==1);
 assert(state.text=="空闲" && mode.text=="自动");
 d.SetStatus(Lang::Strings::SPEAKING);assert(state.text=="说话中");assert_frame();
 // Normal fallback without explicit metadata.
 assert(animation=="speaking");
 // Metadata can arrive before audio START/SetStatus(SPEAKING).
 for(const char* emotion : {"jealous","protect","curious"}){
  d.SetStatus(Lang::Strings::LISTENING);d.SetEmotion("neutral");
  assert(animation=="listening");
  d.SetEmotion(emotion);d.SetStatus(Lang::Strings::SPEAKING);
  assert(animation==emotion && state.text=="说话中" && mode.text=="自动");assert_frame();
  d.ShowNotification("notice");assert(animation==emotion);
  // Repeated status does not erase this turn's expression.
  d.SetStatus(Lang::Strings::SPEAKING);assert(animation==emotion);
  // Genuine next listening transition clears the previous turn.
  d.SetStatus(Lang::Strings::LISTENING);assert(animation=="listening");
  d.SetEmotion("neutral");d.SetStatus(Lang::Strings::SPEAKING);
  assert(animation=="speaking");
  // Reverse ordering remains supported.
  d.SetEmotion(emotion);assert(animation==emotion && state.text=="说话中");
  d.SetStatus(Lang::Strings::STANDBY);d.SetEmotion("neutral");assert(animation=="idle");
  d.SetStatus(Lang::Strings::SPEAKING);assert(animation=="speaking");
 }
 // Touch dialogs retain their separate overlay lifetime and do not select a
 // base expression or leak an explicit-expression latch into the next turn.
 assert(d.InsertAnimDialog("protect",3000));assert(animation=="speaking");
 d.SetEmotion("protect");d.LoadAssets();d.SetStatus(Lang::Strings::SPEAKING);
 assert(animation=="speaking" && state.text=="说话中");
 // Explicit neutral/state animation resets preserve their existing meaning.
 d.SetEmotion("protect");d.SetEmotion("neutral");assert(animation=="speaking");
 d.SetEmotion("missing");d.SetStatus(Lang::Strings::SPEAKING);assert(animation=="speaking");
 d.SetStatus(nullptr);assert(!state.visible && state.text.empty());
 d.UnmountAssets();assert(font_live==0);
 assert(events[events.size()-3]=="unload" && events[events.size()-2]=="free" && events.back()=="unmount");
 }
 assert(font_live==0);
 mounted=true;load_failure=true;
 {emote::EmoteDisplay d;d.LoadAssets();assert(!loaded && font_live==0);
 d.SetEmotion("neutral");d.SetStatus(Lang::Strings::LISTENING);
 assert(!d.InsertAnimDialog("happy",10));
 d.SetEmotion(nullptr);d.ShowNotification(nullptr);assert(!d.InsertAnimDialog(nullptr,10));
 load_failure=false;d.LoadAssets();assert(loaded && font_live==1);}
 assert(!loaded && font_live==0);
 mounted=true;create_failure=true;
 {emote::EmoteDisplay d;d.LoadAssets();assert(!loaded && font_live==0);
 create_failure=false;d.LoadAssets();assert(loaded && font_live==1);}
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
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_layout_and_application_use_real_mode(self):
        layout = json.loads((ROOT / "main/boards/lckfb/szpi-esp32s3/assets/320_240/layout.json").read_text())
        labels = {item["name"]: item for item in layout}
        self.assertNotIn("mode_label",labels)
        self.assertNotIn("state_label",labels)
        display_source=(ROOT/"main/display/emote_display.cc").read_text()
        source = (ROOT / "main/application.cc").read_text()
        body = method(source, "void Application::SetListeningMode")
        self.assertIn("SetInteractionMode(mode != kListeningModeManualStop)",body)
        self.assertIn("SetInteractionMode(listening_mode_ != kListeningModeManualStop)",source)
        # No synthetic state: display gets exactly the status emitted by application.
        self.assertIn("display->SetStatus(Lang::Strings::LISTENING)",source)
        self.assertIn("display->SetStatus(Lang::Strings::STANDBY)",source)

if __name__ == "__main__":
    unittest.main()
