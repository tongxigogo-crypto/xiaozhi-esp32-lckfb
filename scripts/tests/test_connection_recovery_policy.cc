#include <cassert>
#include <cstdint>
#include <initializer_list>

#include "../../main/protocols/connection_recovery.h"

using xiaozhi::ConnectionRecoveryPolicy;
using xiaozhi::RecoveryActionKind;
using xiaozhi::RecoveryListeningMode;

static void expect_start(const xiaozhi::RecoveryAction& action, uint64_t generation,
                         RecoveryListeningMode mode) {
    assert(action.kind == RecoveryActionKind::kStartOpen);
    assert(action.generation == generation);
    assert(action.mode == mode);
}

int main() {
    ConnectionRecoveryPolicy policy;

    // A continuous session keeps its exact mode after an unexpected close.
    const auto start = policy.StartContinuous(RecoveryListeningMode::kRealtime, false);
    const auto generation = start.generation;
    expect_start(start, generation, RecoveryListeningMode::kRealtime);
    assert(policy.OpenSucceeded(generation).kind == RecoveryActionKind::kRestoreListening);

    const auto first_close = policy.UnexpectedClose();
    assert(first_close.kind == RecoveryActionKind::kScheduleRetry);
    assert(first_close.delay_ms == 1000);
    assert(first_close.attempt == 1);
    assert(policy.UnexpectedClose().kind == RecoveryActionKind::kNone);

    const auto attempt1 = policy.RetryDue(generation);
    expect_start(attempt1, generation, RecoveryListeningMode::kRealtime);
    const auto second_close = policy.OpenFailed(generation);
    assert(second_close.kind == RecoveryActionKind::kScheduleRetry);
    assert(second_close.delay_ms == 2000);

    // A stale completion cannot affect a newer explicit session.
    const auto cancel = policy.Cancel();
    assert(cancel.kind == RecoveryActionKind::kCancel);
    const auto manual = policy.StartManual(false);
    const auto manual_generation = manual.generation;
    expect_start(manual, manual_generation, RecoveryListeningMode::kManualStop);
    assert(policy.OpenSucceeded(generation).kind == RecoveryActionKind::kNone);
    assert(policy.OpenFailed(generation).kind == RecoveryActionKind::kNone);
    assert(policy.OpenSucceeded(manual_generation).kind == RecoveryActionKind::kNone);

    // A manual press/release cancels a pending backoff immediately; an old
    // timer and its completion cannot start or close the manual session.
    ConnectionRecoveryPolicy pending;
    const auto pending_start = pending.StartContinuous(RecoveryListeningMode::kRealtime, false);
    assert(pending.OpenSucceeded(pending_start.generation).kind ==
           RecoveryActionKind::kRestoreListening);
    assert(pending.UnexpectedClose().kind == RecoveryActionKind::kScheduleRetry);
    assert(pending.Cancel().kind == RecoveryActionKind::kCancel);
    const auto manual_after_cancel = pending.StartManual(false);
    assert(pending.RetryDue(pending_start.generation).kind == RecoveryActionKind::kNone);
    assert(pending.UnexpectedClose().kind == RecoveryActionKind::kNone);
    assert(pending.OpenSucceeded(manual_after_cancel.generation).kind == RecoveryActionKind::kNone);

    // Retry exhaustion is finite and remains idle until new explicit intent.
    ConnectionRecoveryPolicy exhausted;
    const auto boot = exhausted.StartContinuous(RecoveryListeningMode::kAutoStop, false);
    assert(exhausted.OpenSucceeded(boot.generation).kind == RecoveryActionKind::kRestoreListening);
    const auto delays = {1000u, 2000u, 4000u, 8000u, 16000u};
    unsigned expected_attempt = 1;
    auto scheduled = exhausted.UnexpectedClose();
    for (const auto expected_delay : delays) {
        assert(scheduled.kind == RecoveryActionKind::kScheduleRetry);
        assert(scheduled.delay_ms == expected_delay);
        assert(scheduled.attempt == expected_attempt);
        const auto open = exhausted.RetryDue(boot.generation);
        expect_start(open, boot.generation, RecoveryListeningMode::kAutoStop);
        const auto failed = exhausted.OpenFailed(boot.generation);
        if (expected_attempt < 5) {
            assert(failed.kind == RecoveryActionKind::kScheduleRetry);
        } else {
            assert(failed.kind == RecoveryActionKind::kExhausted);
        }
        scheduled = failed;
        ++expected_attempt;
    }
    assert(!exhausted.HasContinuousIntent());
    assert(exhausted.UnexpectedClose().kind == RecoveryActionKind::kNone);

    return 0;
}
