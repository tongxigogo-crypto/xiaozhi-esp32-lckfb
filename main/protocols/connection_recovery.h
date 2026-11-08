#ifndef _CONNECTION_RECOVERY_H_
#define _CONNECTION_RECOVERY_H_

#include <cstdint>

namespace xiaozhi {

// Kept independent of Protocol/ESP-IDF types so the lifecycle policy can run
// in a deterministic host test and cannot accidentally acquire board state.
enum class RecoveryListeningMode : uint8_t {
    kAutoStop,
    kManualStop,
    kRealtime,
};

enum class RecoveryActionKind : uint8_t {
    kNone,
    kStartOpen,
    kScheduleRetry,
    kRestoreListening,
    kCancel,
    kExhausted,
};

struct RecoveryAction {
    RecoveryActionKind kind = RecoveryActionKind::kNone;
    uint64_t generation = 0;
    RecoveryListeningMode mode = RecoveryListeningMode::kAutoStop;
    uint32_t delay_ms = 0;
    uint8_t attempt = 0;
};

// Main-task-owned slot: intent generations cancel meaning, job IDs retire ownership.
class RecoveryJobSlot {
public:
    uint64_t Begin() {
        if (active_ != 0)
            return 0;
        if (++next_ == 0)
            ++next_;
        return active_ = next_;
    }
    bool Retire(uint64_t job) {
        if (job == 0 || job != active_)
            return false;
        active_ = 0;
        return true;
    }
    bool busy() const { return active_ != 0; }

private:
    uint64_t next_ = 0;
    uint64_t active_ = 0;
};

class ConnectionRecoveryPolicy {
public:
    static constexpr uint8_t kMaxRecoveryAttempts = 5;

    RecoveryAction StartContinuous(RecoveryListeningMode mode, bool channel_open);
    RecoveryAction StartManual(bool channel_open);
    RecoveryAction UnexpectedClose();
    RecoveryAction RetryDue(uint64_t generation);
    RecoveryAction OpenSucceeded(uint64_t generation);
    RecoveryAction OpenFailed(uint64_t generation);
    RecoveryAction Cancel();

    bool HasContinuousIntent() const { return continuous_intent_; }
    bool IsOpening() const { return opening_; }
    bool IsRetryPending() const { return retry_pending_; }
    bool IsChannelOpen() const { return channel_open_; }
    bool IsGenerationCurrent(uint64_t generation) const { return generation == generation_; }
    RecoveryListeningMode mode() const { return mode_; }
    uint64_t generation() const { return generation_; }
    uint8_t attempt() const { return attempt_; }

private:
    static uint32_t DelayForAttempt(uint8_t attempt);
    uint64_t NextGeneration();
    RecoveryAction StartOpenAction() const;
    RecoveryAction ScheduleRetryAction() const;

    uint64_t generation_ = 0;
    RecoveryListeningMode mode_ = RecoveryListeningMode::kAutoStop;
    bool continuous_intent_ = false;
    bool channel_open_ = false;
    bool opening_ = false;
    bool retry_pending_ = false;
    bool recovery_armed_ = false;
    uint8_t attempt_ = 0;
};

}  // namespace xiaozhi

#endif  // _CONNECTION_RECOVERY_H_
