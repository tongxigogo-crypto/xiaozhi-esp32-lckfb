#include "connection_recovery.h"

namespace xiaozhi {

uint64_t ConnectionRecoveryPolicy::NextGeneration() {
    ++generation_;
    if (generation_ == 0) {
        ++generation_;
    }
    return generation_;
}

uint32_t ConnectionRecoveryPolicy::DelayForAttempt(uint8_t attempt) {
    if (attempt == 0 || attempt > kMaxRecoveryAttempts) {
        return 0;
    }
    return 1000U << (attempt - 1);
}

RecoveryAction ConnectionRecoveryPolicy::StartOpenAction() const {
    return {.kind = RecoveryActionKind::kStartOpen,
            .generation = generation_,
            .mode = mode_,
            .delay_ms = 0,
            .attempt = attempt_};
}

RecoveryAction ConnectionRecoveryPolicy::ScheduleRetryAction() const {
    return {.kind = RecoveryActionKind::kScheduleRetry,
            .generation = generation_,
            .mode = mode_,
            .delay_ms = DelayForAttempt(attempt_),
            .attempt = attempt_};
}

RecoveryAction ConnectionRecoveryPolicy::StartContinuous(RecoveryListeningMode mode,
                                                         bool channel_open) {
    NextGeneration();
    mode_ = mode;
    continuous_intent_ = true;
    channel_open_ = channel_open;
    opening_ = !channel_open;
    retry_pending_ = false;
    recovery_armed_ = channel_open;
    attempt_ = 0;
    if (channel_open) {
        return {};
    }
    return StartOpenAction();
}

RecoveryAction ConnectionRecoveryPolicy::StartManual(bool channel_open) {
    NextGeneration();
    mode_ = RecoveryListeningMode::kManualStop;
    continuous_intent_ = false;
    channel_open_ = channel_open;
    opening_ = !channel_open;
    retry_pending_ = false;
    recovery_armed_ = false;
    attempt_ = 0;
    if (channel_open) {
        return {};
    }
    return StartOpenAction();
}

RecoveryAction ConnectionRecoveryPolicy::UnexpectedClose() {
    if (!continuous_intent_ || !recovery_armed_ || !channel_open_ || opening_ || retry_pending_) {
        return {};
    }

    channel_open_ = false;
    attempt_ = 1;
    retry_pending_ = true;
    return ScheduleRetryAction();
}

RecoveryAction ConnectionRecoveryPolicy::RetryDue(uint64_t generation) {
    if (generation != generation_ || !continuous_intent_ || !retry_pending_ || opening_) {
        return {};
    }

    retry_pending_ = false;
    opening_ = true;
    return StartOpenAction();
}

RecoveryAction ConnectionRecoveryPolicy::OpenSucceeded(uint64_t generation) {
    if (generation != generation_ || !opening_) {
        return {};
    }

    opening_ = false;
    retry_pending_ = false;
    channel_open_ = true;
    recovery_armed_ = continuous_intent_;
    attempt_ = 0;
    if (!continuous_intent_) {
        return {};
    }
    return {
        .kind = RecoveryActionKind::kRestoreListening, .generation = generation_, .mode = mode_};
}

RecoveryAction ConnectionRecoveryPolicy::OpenFailed(uint64_t generation) {
    if (generation != generation_ || !opening_) {
        return {};
    }

    opening_ = false;
    channel_open_ = false;
    // An initial explicit open failure is not an unexpected transport loss.
    // Leave the device idle until a new explicit intent is supplied.
    if (!recovery_armed_) {
        continuous_intent_ = false;
        return {};
    }

    if (attempt_ >= kMaxRecoveryAttempts) {
        continuous_intent_ = false;
        retry_pending_ = false;
        recovery_armed_ = false;
        return {.kind = RecoveryActionKind::kExhausted,
                .generation = generation_,
                .mode = mode_,
                .attempt = attempt_};
    }

    ++attempt_;
    retry_pending_ = true;
    return ScheduleRetryAction();
}

RecoveryAction ConnectionRecoveryPolicy::Cancel() {
    const bool had_work = continuous_intent_ || channel_open_ || opening_ || retry_pending_;
    NextGeneration();
    continuous_intent_ = false;
    channel_open_ = false;
    opening_ = false;
    retry_pending_ = false;
    recovery_armed_ = false;
    attempt_ = 0;
    return had_work ? RecoveryAction{.kind = RecoveryActionKind::kCancel,
                                     .generation = generation_,
                                     .mode = mode_}
                    : RecoveryAction{};
}

}  // namespace xiaozhi
