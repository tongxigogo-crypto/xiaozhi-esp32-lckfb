"""Execute production protocol initialization/JSON dispatch and MQTT goodbye callbacks."""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def extract_method(source, name):
    match = re.search(r"(?:void|bool) Application::" + name + r"\(", source)
    start = match.start()
    brace = source.index("{", start)
    depth, pos = 1, brace + 1
    while depth:
        depth += (source[pos] == "{") - (source[pos] == "}")
        pos += 1
    return source[start:pos]


ADAPTER = r'''
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstring>
#include <deque>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include "connection_recovery.h"
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGE(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
#define cJSON_ArrayForEach(item, array) for(item=nullptr; item!=nullptr;)
struct cJSON {
    const char* valuestring=nullptr; double valuedouble=0;
    bool object=true;
    std::map<std::string,cJSON> children;
};
cJSON String(const char* text) { cJSON n; n.object=false; n.valuestring=text; return n; }
cJSON Message(const char* type) { cJSON n; n.children["type"]=String(type); return n; }
cJSON* cJSON_GetObjectItem(const cJSON* n,const char* key) {
    if(!n) return nullptr;
    auto it=n->children.find(key);
    return it==n->children.end()?nullptr:const_cast<cJSON*>(&it->second);
}
bool cJSON_IsString(const cJSON* n) { return n && n->valuestring; }
bool cJSON_IsObject(const cJSON* n) { return n && n->object; }
bool cJSON_IsNumber(const cJSON*) { return false; }
bool cJSON_IsArray(const cJSON*) { return false; }
void cJSON_Delete(cJSON* n) { delete n; }
cJSON* cJSON_Duplicate(const cJSON* n,bool) { return new cJSON(*n); }
std::map<std::string,cJSON> fixtures;
cJSON* cJSON_Parse(const char* text) { return cJSON_Duplicate(&fixtures.at(text),true); }
struct TextGlyph {};
struct TextGlyphPayload { static bool Parse(const cJSON*,std::vector<TextGlyph>&,uint8_t&) {return false;} };
struct NotifySubtitle { uint32_t start_ms; std::string text; };
struct AudioStreamPacket {};
enum State { kDeviceStateIdle,kDeviceStateSpeaking,kDeviceStateListening,kDeviceStateConnecting };
enum ListeningMode { kListeningModeManualStop,kListeningModeRealtime };
enum PowerSaveLevel { PERFORMANCE };
namespace Lang { namespace Strings { constexpr auto LOADING_PROTOCOL="loading"; }
namespace Sounds { constexpr auto OGG_VIBRATION="vibration"; } }
struct Display {
    void SetStatus(const char*) {} void SetEmotion(const char*) {}
    void AddTextGlyphs(const std::vector<TextGlyph>&,uint8_t) {}
    void SetChatMessage(const char*,const char*) {}
};
struct Codec { int output_sample_rate() { return 24000; } };
struct Board {
    static Board& GetInstance() { static Board b; return b; }
    Display* GetDisplay() { static Display d; return &d; }
    Codec* GetAudioCodec() { static Codec c; return &c; }
    void SetPowerSaveLevel(PowerSaveLevel) {}
};
struct Ota {
    bool mqtt=true;
    bool HasMqttConfig() {return mqtt;} bool HasWebsocketConfig() {return !mqtt;}
};
struct Audio { int packets=0; void PushPacketToDecodeQueue(std::unique_ptr<AudioStreamPacket>) {++packets;} };
struct Protocol {
    uint64_t epoch=0; bool opened=false; int closes=0;
    std::function<void(uint64_t,const cJSON*)> on_incoming_json_epoch_;
    std::function<void(const cJSON*)> on_incoming_json_;
    std::function<void(uint64_t,std::unique_ptr<AudioStreamPacket>)> audio;
    std::function<void(uint64_t)> on_open,on_close;
    virtual ~Protocol()=default;
    uint64_t ConnectionEpoch() const {return epoch;}
    bool IsAudioChannelOpened() const {return opened;}
    void CancelOpenAudioChannel() {++epoch;opened=false;}
    void CloseAudioChannel(bool=true) {++closes;opened=false;}
    int server_sample_rate() const {return 24000;}
    void OnConnected(std::function<void()>) {}
    void OnNetworkError(std::function<void(const std::string&)>) {}
    void OnIncomingAudioWithEpoch(decltype(audio) f) {audio=std::move(f);}
    void OnAudioChannelOpenedWithEpoch(decltype(on_open) f) {on_open=std::move(f);}
    void OnAudioChannelClosedWithEpoch(decltype(on_close) f) {on_close=std::move(f);}
    void OnIncomingJsonWithEpoch(decltype(on_incoming_json_epoch_) f) {on_incoming_json_epoch_=std::move(f);}
    void Start() {}
    void Json(const cJSON& n) {on_incoming_json_epoch_(epoch,&n);}
};
struct MqttTransport {
    std::function<void(const std::string&,const std::string&)> message;
    void OnMessage(decltype(message) f) {message=std::move(f);}
};
struct MqttProtocol: Protocol {
    std::unique_ptr<MqttTransport> mqtt_=std::make_unique<MqttTransport>();
    std::string session_id_="old";
    std::shared_ptr<bool> alive_=std::make_shared<bool>(true);
    std::chrono::steady_clock::time_point last_incoming_time_;
    void ParseServerHello(const cJSON*) {}
    void InstallMessageHandler();
};
struct WebsocketProtocol: Protocol {};
struct McpServer {
    int messages=0;
    static McpServer& GetInstance() {static McpServer m;return m;}
    void ParseMessage(const cJSON*) {++messages;}
};
constexpr int MAIN_EVENT_ERROR=1;
void xEventGroupSetBits(int,int) {}
class Application {
public:
    static Application* current;
    static Application& GetInstance() {return *current;}
    Application() {current=this;}
    std::shared_ptr<Protocol> protocol_;
    std::unique_ptr<Ota> ota_=std::make_unique<Ota>();
    Audio audio_service_;
    State state=kDeviceStateIdle;
    ListeningMode listening_mode_=kListeningModeRealtime;
    std::atomic<bool> recovery_worker_active_{false};
    std::atomic<Protocol*> accepted_protocol_{nullptr};
    std::atomic<uint64_t> accepted_connection_epoch_{0},recovery_generation_token_{0};
    xiaozhi::ConnectionRecoveryPolicy recovery_policy_;
    bool aborted_=false,pending_manual_start_=false;
    std::string last_error_message_,pending_wake_word_;
    int event_group_=0,notifications=0,reboots=0;
    std::deque<std::function<void()>> events;
    void Schedule(std::function<void()> f) {events.push_back(std::move(f));}
    void Step() {assert(!events.empty());auto f=std::move(events.front());events.pop_front();f();}
    void Drain() {while(!events.empty()) Step();}
    State GetDeviceState() const {return state;}
    void SetDeviceState(State s) {state=s;}
    void DismissAlert() {}
    void HandleAudioChannelClosed(uint64_t) {}
    void StartNotification(std::string,std::vector<NotifySubtitle>) {++notifications;}
    void Reboot() {++reboots;}
    void Alert(const char*,const char*,const char*,const char*) {}
    void InitializeProtocol();
    void CancelRecoveryIntent(bool preserve_channel=false);
    bool IsCurrentProtocolSource(const std::weak_ptr<Protocol>&,uint64_t) const;
    bool IsCurrentControlSource(const std::weak_ptr<Protocol>&,uint64_t) const;
};
Application* Application::current=nullptr;
'''

CASES = r'''
int main(int argc,char** argv) {
    assert(argc==2); const std::string scenario=argv[1];
    Application a;
    cJSON mcp=Message("mcp"); mcp.children["payload"]=cJSON{};
    if(scenario=="idle_mqtt") {
        a.InitializeProtocol();
        assert(a.protocol_->epoch==0 && !a.protocol_->opened);
        a.protocol_->Json(mcp);
        cJSON notify=Message("notify");notify.children["audio_url"]=String("test");
        a.protocol_->Json(notify);
        cJSON system=Message("system");system.children["command"]=String("reboot");
        a.protocol_->Json(system);a.Drain();
        assert(McpServer::GetInstance().messages==1 && a.notifications==1 && a.reboots==1);
    } else if(scenario=="ws_early_mcp") {
        a.ota_->mqtt=false;a.InitializeProtocol();
        a.protocol_->epoch=1;a.protocol_->opened=true;
        a.protocol_->Json(mcp); // hello completed; receiver beats opened/acceptance event
        a.Step();assert(McpServer::GetInstance().messages==1);
        assert(a.accepted_connection_epoch_==0);
        a.protocol_->on_open(1);a.Drain();assert(a.accepted_connection_epoch_==1);
    } else if(scenario=="stale_json") {
        a.InitializeProtocol();a.protocol_->epoch=1;a.protocol_->opened=true;
        a.protocol_->on_open(1);a.Drain();
        cJSON tts=Message("tts");tts.children["state"]=String("start");
        a.protocol_->Json(mcp);a.protocol_->Json(tts);
        a.CancelRecoveryIntent();a.Drain();
        assert(McpServer::GetInstance().messages==0 && a.state==kDeviceStateIdle);
        auto old=a.protocol_;old->Json(mcp);a.InitializeProtocol();a.Drain();
        assert(McpServer::GetInstance().messages==0);
        cJSON notify=Message("notify");notify.children["audio_url"]=String("test");
        a.protocol_->Json(notify);a.Step(); // first dispatch schedules a second mutation
        a.CancelRecoveryIntent();a.Drain();assert(a.notifications==0);
    } else if(scenario=="audio_gate") {
        a.InitializeProtocol();
        cJSON tts=Message("tts");tts.children["state"]=String("start");
        a.protocol_->Json(tts);a.Drain();assert(a.state==kDeviceStateIdle);
        a.state=kDeviceStateSpeaking;
        a.protocol_->audio(0,std::make_unique<AudioStreamPacket>());a.Drain();
        assert(a.audio_service_.packets==0);
        a.state=kDeviceStateIdle;a.protocol_->epoch=1;a.protocol_->opened=true;
        a.protocol_->on_open(1);a.Drain();
        a.protocol_->Json(tts);a.Drain();assert(a.state==kDeviceStateSpeaking);
        a.protocol_->audio(1,std::make_unique<AudioStreamPacket>());
        assert(a.audio_service_.packets==1);
    } else if(scenario=="mqtt_goodbye") {
        MqttProtocol p;p.epoch=1;p.opened=true;p.InstallMessageHandler();
        cJSON goodbye=Message("goodbye");goodbye.children["session_id"]=String("old");
        fixtures["goodbye"]=goodbye;
        p.mqtt_->message("topic","goodbye");
        p.session_id_="new";a.Drain();assert(p.closes==0 && p.opened);
        goodbye.children["session_id"]=String("new");fixtures["goodbye"]=goodbye;
        p.mqtt_->message("topic","goodbye");
        ++p.epoch;a.Drain();assert(p.closes==0 && p.opened); // reused ID, newer epoch
        p.mqtt_->message("topic","goodbye");a.Drain();assert(p.closes==1 && !p.opened);
    } else {assert(false);}
}
'''


class ConnectionRecoveryDispatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("clang++") or shutil.which("c++")
        if not compiler:
            raise unittest.SkipTest("host C++ compiler unavailable")
        cls.directory = tempfile.TemporaryDirectory(prefix="xiaozhi-dispatch-")
        cls.addClassCleanup(cls.directory.cleanup)
        cpp = Path(cls.directory.name) / "dispatch.cc"
        cls.executable = Path(cls.directory.name) / "dispatch"
        app = (ROOT / "main/application.cc").read_text()
        names = ["InitializeProtocol", "CancelRecoveryIntent", "IsCurrentProtocolSource"]
        if "bool Application::IsCurrentControlSource(" in app:
            names.append("IsCurrentControlSource")
        mqtt = (ROOT / "main/protocols/mqtt_protocol.cc").read_text()
        start = mqtt.index("    mqtt_->OnMessage(")
        callback = mqtt[start:mqtt.index("\n    });", start) + len("\n    });")]
        cpp.write_text(ADAPTER + "\n".join(extract_method(app,n) for n in names)
                       + "\nvoid MqttProtocol::InstallMessageHandler() {\n" + callback + "\n}\n" + CASES)
        subprocess.run([compiler,"-std=c++17","-Wall","-Wextra","-Werror","-Wno-unused-parameter",
                        "-I",str(ROOT / "main/protocols"),str(cpp),
                        str(ROOT / "main/protocols/connection_recovery.cc"),
                        "-o",str(cls.executable)],check=True)

    def run_scenario(self,name):
        subprocess.run([str(self.executable),name],check=True)

    def test_idle_mqtt_dispatches_control_without_audio_epoch(self):
        self.run_scenario("idle_mqtt")

    def test_ws_initial_mcp_dispatches_before_opened_event(self):
        self.run_scenario("ws_early_mcp")

    def test_cancelled_and_replaced_json_stays_rejected(self):
        self.run_scenario("stale_json")

    def test_audio_and_tts_require_accepted_session(self):
        self.run_scenario("audio_gate")

    def test_mqtt_queued_goodbye_cannot_close_replacement_session(self):
        self.run_scenario("mqtt_goodbye")


if __name__ == "__main__":
    unittest.main()
