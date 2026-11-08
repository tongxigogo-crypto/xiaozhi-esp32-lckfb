"""Run real Application control methods against deterministic hardware adapters."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_connection_recovery_lifecycle import PREAMBLE, ROOT, method


ADAPTER = PREAMBLE.replace(
    'enum State { kDeviceStateIdle, kDeviceStateConnecting, kDeviceStateListening };',
    '''enum State { kDeviceStateIdle, kDeviceStateConnecting, kDeviceStateListening,
    kDeviceStateSpeaking, kDeviceStateNotifying, kDeviceStateActivating,
    kDeviceStateWifiConfiguring, kDeviceStateAudioTesting, kDeviceStateStarting,
    kDeviceStateUpgrading };
enum AecMode { kAecOff, kAecOnServerSide, kAecOnDeviceSide };
enum AbortReason { kAbortReasonNone };
enum PowerSaveLevel { PERFORMANCE, LOW_POWER };
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGE(...) ((void)0)
namespace Lang { namespace Strings {
constexpr auto RTC_MODE_OFF="off", RTC_MODE_ON="on", OTA_UPGRADE="ota",
UPGRADING="upgrade", NEW_VERSION="version", ERROR="error", UPGRADE_FAILED="failed";
} namespace Sounds { constexpr auto OGG_UPGRADE="upgrade", OGG_EXCLAMATION="error"; } }
struct Display {
    void UpdateStatusBar(bool) {} void ShowNotification(const char*) {}
    void SetChatMessage(const char*, const char*) {}
};
struct Board {
    static Board& GetInstance() { static Board b; return b; }
    Display* GetDisplay() { static Display d; return &d; }
    void SetPowerSaveLevel(PowerSaveLevel) {}
};
struct Ota { static bool Upgrade(const std::string&, std::function<void(int,size_t)>) { return false; } };
xiaozhi::RecoveryListeningMode ToRecoveryMode(ListeningMode m) {
    return static_cast<xiaozhi::RecoveryListeningMode>(m);
}''',
).replace('int opens=0;', 'int opens=0, closes=0, stops=0;').replace(
    'void CloseAudioChannel() { CancelOpenAudioChannel(); }',
    '''void CloseAudioChannel() { ++closes; CancelOpenAudioChannel(); }
    void SendStopListening() { ++stops; }''',
).replace('int resets=0;', '''int resets=0;
    void EnableAudioTesting(bool) {} void EnableDeviceAec(bool) {}
    void Stop() {} void Start() {}''').replace(
    'void HandleStartListeningEvent() { ++manual; }',
    '''void HandleStartListeningEvent();
    void HandleToggleChatEvent();
    void HandleStopListeningEvent();
    void HandleNetworkDisconnectedEvent();
    void SetAecMode(AecMode);
    bool UpgradeFirmware(const std::string&, const std::string&);
    AecMode aec_mode_=kAecOff;
    ListeningMode listening_mode_=kListeningModeRealtime;
    ListeningMode GetDefaultListeningMode() const { return kListeningModeRealtime; }
    void ContinueOpenAudioChannel(ListeningMode);
    void StopNotification() { state=kDeviceStateIdle; }
    void AbortSpeaking(AbortReason) {}
    void Alert(const char*,const char*,const char*,const char*) {}
    void Reboot() { assert(false); }''',
).replace(
    'void SetListeningMode(ListeningMode) { ++restored; state=kDeviceStateListening; }',
    'void SetListeningMode(ListeningMode m) { listening_mode_=m; ++restored; state=kDeviceStateListening; }',
)

CASES = r'''
int main(int argc, char** argv) {
    assert(argc==2);
    Application a; a.Start(); a.RunWorker(); a.Drain();
    auto source=std::weak_ptr<Protocol>(a.protocol_);
    const auto epoch=a.protocol_->ConnectionEpoch();
    const std::string scenario=argv[1];
    if(scenario=="toggle") {
        a.HandleToggleChatEvent(); a.HandleAudioChannelClosed(epoch); a.Drain();
        assert(a.state==kDeviceStateIdle);
        assert(a.protocol_->closes==1);
        assert(!a.IsCurrentProtocolSource(source,epoch));
    } else if(scenario=="manual") {
        a.state=kDeviceStateSpeaking;
        a.HandleStartListeningEvent(); a.Drain();
        assert(a.state==kDeviceStateListening && a.listening_mode_==kListeningModeManualStop);
        assert(a.protocol_->closes==0 && a.protocol_->opens==1);
        assert(a.IsCurrentProtocolSource(source,epoch)); // queued TTS/audio remains receivable
        a.protocol_->CloseAudioChannel(); a.HandleAudioChannelClosed(epoch); a.Drain();
        assert(a.state==kDeviceStateIdle);
    } else if(scenario=="manual_closed") {
        a.state=kDeviceStateSpeaking;
        a.protocol_->opened=false; // transport lost before its close is consumed
        a.HandleStartListeningEvent(); a.Drain();
        assert(a.state==kDeviceStateConnecting && a.recovery_worker_active_);
        a.RunWorker(); a.Drain();
        assert(a.state==kDeviceStateListening && a.listening_mode_==kListeningModeManualStop);
        assert(a.protocol_->opens==2);
        assert(a.IsCurrentProtocolSource(source,a.protocol_->ConnectionEpoch()));
    } else if(scenario=="manual_idle") {
        a.HandleStopListeningEvent(); a.HandleStartListeningEvent(); a.Drain();
        assert(a.state==kDeviceStateListening && a.listening_mode_==kListeningModeManualStop);
        assert(a.protocol_->opens==1 && a.IsCurrentProtocolSource(source,epoch));
    } else if(scenario=="aec") {
        a.SetAecMode(kAecOnServerSide); a.Drain();
        assert(a.protocol_->closes==1);
        assert(!a.IsCurrentProtocolSource(source,epoch) && a.state==kDeviceStateIdle);
        a.HandleAudioChannelClosed(epoch); a.Drain();
    } else if(scenario=="upgrade") {
        assert(!a.UpgradeFirmware("candidate", "test")); a.Drain();
        assert(a.protocol_->closes==1);
        assert(!a.IsCurrentProtocolSource(source,epoch));
        a.HandleAudioChannelClosed(epoch); a.Drain();
    } else if(scenario=="stop") {
        a.HandleStopListeningEvent(); a.Drain();
        assert(a.state==kDeviceStateIdle && a.protocol_->stops==1);
    } else if(scenario=="network") {
        a.HandleNetworkDisconnectedEvent(); a.Drain();
        assert(a.state==kDeviceStateIdle && a.recovery_worker_active_);
        a.CancelRecoveryIntent(); a.RunWorker(); a.Drain();
    } else { assert(false); }
    assert(!a.recovery_policy_.HasContinuousIntent());
    assert(!a.recovery_policy_.IsRetryPending());
    assert(!a.recovery_worker_active_ && workers.empty());
}
'''


class ConnectionRecoveryControlsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("clang++") or shutil.which("c++")
        if not compiler:
            raise unittest.SkipTest("host C++ compiler unavailable")
        source = (ROOT / "main/application.cc").read_text()
        cls.directory = tempfile.TemporaryDirectory(prefix="xiaozhi-controls-")
        cls.addClassCleanup(cls.directory.cleanup)
        cpp = Path(cls.directory.name) / "controls.cc"
        cls.executable = Path(cls.directory.name) / "controls"
        names = (
            "StartRecoveryTask", "HandleRecoveryOpenResult", "HandleRecoveryRetryTimer",
            "HandleRecoveryWorkerDone", "HandleAudioChannelClosed", "CancelRecoveryIntent",
            "IsCurrentProtocolSource", "HandleToggleChatEvent", "HandleStartListeningEvent",
            "HandleStopListeningEvent", "HandleNetworkDisconnectedEvent", "SetAecMode",
            "ContinueOpenAudioChannel",
        )
        upgrade = method(source, "UpgradeFirmware")
        # Match the real cancellation API, including its default argument.
        header = (ROOT / "main/application.h").read_text()
        declaration = next(line.strip() for line in header.splitlines() if "void CancelRecoveryIntent(" in line)
        adapter = ADAPTER.replace("void CancelRecoveryIntent(bool preserve_channel = false);", declaration)
        cpp.write_text(adapter + "\n".join(method(source, n) for n in names) + upgrade + CASES)
        subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        "-Wno-format", "-I", str(ROOT / "main/protocols"), str(cpp),
                        str(ROOT / "main/protocols/connection_recovery.cc"),
                        "-o", str(cls.executable)], check=True)

    def run_scenario(self, name):
        subprocess.run([str(self.executable), name], check=True)

    def test_toggle_stop_enters_idle_once(self):
        self.run_scenario("toggle")

    def test_speaking_to_manual_retains_inbound_epoch_without_retry(self):
        self.run_scenario("manual")

    def test_aec_closes_live_channel_once_without_retry(self):
        self.run_scenario("aec")

    def test_speaking_to_manual_reopens_already_lost_transport(self):
        self.run_scenario("manual_closed")

    def test_manual_start_reuses_idle_live_channel(self):
        self.run_scenario("manual_idle")

    def test_upgrade_closes_live_channel_once_without_retry(self):
        self.run_scenario("upgrade")

    def test_explicit_stop_cancels_recovery(self):
        self.run_scenario("stop")

    def test_network_loss_compiles_atomic_load_and_retries(self):
        self.run_scenario("network")


if __name__ == "__main__":
    unittest.main()
