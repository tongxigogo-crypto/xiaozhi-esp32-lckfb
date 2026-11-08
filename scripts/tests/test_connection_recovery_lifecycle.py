"""Execute the production Application recovery methods with a deterministic RTOS."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def method(source, name):
    kind = "bool" if name in ("IsCurrentProtocolSource", "UpgradeFirmware") else "void"
    start = source.index(kind + " Application::" + name + "(")
    brace = source.index("{", start)
    depth = 1
    pos = brace + 1
    while depth:
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
        pos += 1
    return source[start:pos]


PREAMBLE = r"""
#include <atomic>
#include <cassert>
#include <cstdint>
#include <deque>
#include <functional>
#include <memory>
#include <string>
#include "connection_recovery.h"
enum ListeningMode { kListeningModeAutoStop, kListeningModeManualStop, kListeningModeRealtime };
enum State { kDeviceStateIdle, kDeviceStateConnecting, kDeviceStateListening };
constexpr int pdPASS=1;
#define ESP_LOGW(...) ((void)0)
#define pdMS_TO_TICKS(x) (x)
struct Protocol {
    uint64_t epoch=0, reserved=0;
    bool opened=false;
    int opens=0;
    std::function<void()> during_open;
    uint64_t ReserveAudioChannelOpen() { return reserved=++epoch; }
    void CancelReservedAudioChannelOpen(uint64_t e) { if(e==epoch) CancelOpenAudioChannel(); }
    void CancelOpenAudioChannel() { ++epoch; opened=false; }
    void CloseAudioChannel() { CancelOpenAudioChannel(); }
    uint64_t ConnectionEpoch() const { return epoch; }
    bool IsAudioChannelOpened() const { return opened; }
    bool OpenAudioChannelForEpoch(uint64_t e) {
        ++opens;
        if(during_open) during_open();
        if(e!=epoch || e!=reserved) return false;
        return opened=true;
    }
};
std::deque<std::function<void()>> workers;
std::function<void()> delay_hook;
int task_result=pdPASS;
int xTaskCreate(void (*fn)(void*), const char*, int, void* arg, int, void*) {
    if(task_result!=pdPASS) return 0;
    workers.emplace_back([=] { fn(arg); });
    return pdPASS;
}
void vTaskDelay(uint32_t) {
    if(delay_hook) { auto hook=std::move(delay_hook); delay_hook=nullptr; hook(); }
}
void vTaskDelete(void*) {}
struct Audio {
    int resets=0;
    bool PopPacketFromSendQueue() { return false; }
    void ResetDecoder() { ++resets; }
};
ListeningMode FromRecoveryMode(xiaozhi::RecoveryListeningMode m) {
    return static_cast<ListeningMode>(m);
}
class Application {
public:
    std::shared_ptr<Protocol> protocol_=std::make_shared<Protocol>();
    std::atomic<bool> recovery_worker_active_{false};
    std::atomic<uint64_t> recovery_generation_token_{0}, accepted_connection_epoch_{0};
    std::atomic<Protocol*> accepted_protocol_{nullptr};
    xiaozhi::RecoveryJobSlot recovery_jobs_;
    xiaozhi::ConnectionRecoveryPolicy recovery_policy_;
    Audio audio_service_;
    bool pending_manual_start_=false, play_popup_on_listening_=false;
    bool pending_listening_start_=false;
    std::string pending_wake_word_;
    int restored=0, manual=0, wakes=0;
    State state=kDeviceStateIdle;
    std::deque<std::function<void()>> events;
    struct RecoveryTaskContext {
        Application* app; std::shared_ptr<Protocol> protocol;
        uint64_t generation, job_id, reservation_epoch;
        ListeningMode mode; uint32_t delay_ms; bool retry_timer;
    };
    void Schedule(std::function<void()> f) { events.push_back(std::move(f)); }
    State GetDeviceState() const { return state; }
    void SetDeviceState(State s) { state=s; }
    void SetListeningMode(ListeningMode) { ++restored; state=kDeviceStateListening; }
    void HandleStartListeningEvent() { ++manual; }
    void BeginWakeWordInvoke(const std::string&) { ++wakes; }
    void ContinueWakeWordInvoke(const std::string&) { ++wakes; }
    void StartRecoveryTask(uint64_t, ListeningMode, uint32_t, bool);
    void HandleRecoveryOpenResult(uint64_t, ListeningMode, bool, uint64_t);
    void HandleRecoveryRetryTimer(uint64_t, ListeningMode);
    void HandleRecoveryWorkerDone(uint64_t);
    void HandleAudioChannelClosed(uint64_t);
    void CancelRecoveryIntent(bool preserve_channel = false);
    bool IsCurrentProtocolSource(const std::weak_ptr<Protocol>&, uint64_t) const;
    void Drain() { while(!events.empty()) { auto f=std::move(events.front()); events.pop_front(); f(); } }
    void RunWorker() { assert(!workers.empty()); auto f=std::move(workers.front()); workers.pop_front(); f(); }
    uint64_t Start() {
        auto a=recovery_policy_.StartContinuous(xiaozhi::RecoveryListeningMode::kRealtime,false);
        recovery_generation_token_=a.generation;
        state=kDeviceStateConnecting;
        StartRecoveryTask(a.generation,kListeningModeRealtime,0,false);
        return a.generation;
    }
};
"""
CASES = r"""
int main() {
    // Cancellation before worker entry must not reset/revive the reservation.
    {
        Application a; a.Start(); auto old=a.protocol_;
        a.CancelRecoveryIntent(); a.state=kDeviceStateIdle;
        a.pending_manual_start_=true;
        a.RunWorker(); a.Drain();
        assert(old->opens==0 && a.restored==0 && a.manual==1);
        assert(!a.recovery_worker_active_);
    }
    // A cancelled 16-second backoff releases after one bounded delay slice.
    {
        Application a;
        auto action=a.recovery_policy_.StartContinuous(
            xiaozhi::RecoveryListeningMode::kRealtime,true);
        (void)action;
        auto retry=a.recovery_policy_.UnexpectedClose();
        a.recovery_generation_token_=retry.generation;
        a.StartRecoveryTask(retry.generation,kListeningModeRealtime,16000,true);
        int slices=0;
        delay_hook=[&] { ++slices; a.CancelRecoveryIntent(); a.pending_manual_start_=true; };
        a.RunWorker(); a.Drain();
        assert(slices==1 && a.manual==1 && a.protocol_->opens==0);
    }
    // Duplicate old completion cannot retire a later worker.
    {
        Application a; a.Start(); a.RunWorker();
        auto duplicate=a.events.front();
        a.Drain(); assert(a.restored==1);
        a.CancelRecoveryIntent(); a.Start();
        duplicate();
        assert(a.recovery_worker_active_ && a.recovery_jobs_.busy());
        a.RunWorker(); a.Drain(); assert(a.restored==2);
    }
    // Protocol replacement/reset during open keeps old owner alive, rejects result.
    {
        Application a; a.Start(); std::weak_ptr<Protocol> old=a.protocol_;
        a.protocol_->during_open=[&] {
            a.CancelRecoveryIntent(); a.protocol_=std::make_shared<Protocol>();
        };
        a.RunWorker();
        assert(!old.expired()); // queued result owns the source until consumption
        a.Drain();
        assert(old.expired() && a.restored==0 && !a.recovery_worker_active_);
    }
    // Cancellation after a successful worker but before completion is consumed.
    {
        Application a; a.Start(); a.RunWorker();
        a.CancelRecoveryIntent(); a.state=kDeviceStateIdle; a.Drain();
        assert(a.restored==0 && a.accepted_connection_epoch_==0);
    }
    // Failed task allocation retires ownership and reports an initial failure.
    {
        Application a; task_result=0; a.Start(); task_result=pdPASS;
        assert(!a.recovery_worker_active_ && !a.recovery_jobs_.busy());
        assert(a.state==kDeviceStateIdle && !a.recovery_policy_.HasContinuousIntent());
    }
    // The production queue-consumption gate rejects cancelled and replacement JSON,
    // even if a replacement protocol happens to use the same numeric epoch.
    {
        Application a; a.Start(); a.RunWorker(); a.Drain();
        std::weak_ptr<Protocol> source=a.protocol_;
        uint64_t epoch=a.protocol_->ConnectionEpoch();
        assert(a.IsCurrentProtocolSource(source,epoch));
        std::function<bool()> queued=[&] { return a.IsCurrentProtocolSource(source,epoch); };
        a.CancelRecoveryIntent();
        assert(!queued());
        a.protocol_=std::make_shared<Protocol>();
        a.protocol_->epoch=epoch;
        a.accepted_connection_epoch_=epoch;
        assert(!queued());
    }
    assert(workers.empty());
}
"""


class ConnectionRecoveryLifecycleTest(unittest.TestCase):
    def test_actual_application_lifecycle(self):
        compiler = shutil.which("clang++") or shutil.which("c++")
        if not compiler:
            self.skipTest("host C++ compiler unavailable")
        source = (ROOT / "main/application.cc").read_text()
        methods = "\n".join(method(source, name) for name in (
            "StartRecoveryTask", "HandleRecoveryOpenResult", "HandleRecoveryRetryTimer",
            "HandleRecoveryWorkerDone", "HandleAudioChannelClosed", "CancelRecoveryIntent",
            "IsCurrentProtocolSource",
        ))
        with tempfile.TemporaryDirectory(prefix="xiaozhi-lifecycle-") as directory:
            cpp = Path(directory) / "lifecycle.cc"
            executable = Path(directory) / "lifecycle"
            cpp.write_text(PREAMBLE + methods + CASES)
            subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                            "-I", str(ROOT / "main/protocols"), str(cpp),
                            str(ROOT / "main/protocols/connection_recovery.cc"),
                            "-o", str(executable)], check=True)
            subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    unittest.main()
