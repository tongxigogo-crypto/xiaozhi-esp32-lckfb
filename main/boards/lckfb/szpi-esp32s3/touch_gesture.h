#pragma once

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <functional>
#include <utility>

namespace lckfb_touch {

enum class Gesture {
    kNone,
    // 物理手势 → 枚举名的历史对应关系（2026-11-07 工单2）：
    //   kHappy      = 单击确认
    //   kSurprised  = 双击确认
    //   kAnnoyed    = 长按确认
    //   kLaugh      = 横划确认
    // 枚举名是历史包袱，含义以本注释和 trigger 事件为准；表情映射放在板级。
    kHappy,
    kSurprised,
    kAnnoyed,
    kLaugh,
    // 手指刚接触屏幕（未判定手势）。用于按下瞬间的即时反馈。
    kContact,
};

struct Sample {
    bool valid = false;
    bool down = false;
    int x = 0;
    int y = 0;
    int64_t timestamp_ms = 0;
};

// Polling-friendly recognizer. Invalid controller reads are ignored completely;
// they never synthesize a release event.
class Recognizer {
public:
    static constexpr int64_t kTapMaxDurationMs = 300;
    static constexpr int64_t kDoubleTapWindowMs = 500;
    static constexpr int64_t kLongPressMinDurationMs = 1200;
    static constexpr int kTapMaxDisplacementPx = 10;
    static constexpr int kSwipeMinHorizontalPx = 40;
    static constexpr int kSwipeMaxVerticalPx = 40;
    static constexpr int kReleaseDebounceSamples = 2;

    explicit Recognizer(std::function<void(Gesture)> on_gesture,
                        std::function<void(bool)> on_contact = nullptr)
        : on_gesture_(std::move(on_gesture)), on_contact_(std::move(on_contact)) {}

    void Reset() {
        pressed_ = false;
        release_candidate_ = false;
        release_samples_ = 0;
        waiting_for_double_ = false;
        second_tap_ = false;
        swipe_fired_ = false;
        long_press_fired_ = false;
    }

    void Update(const Sample& sample) {
        if (!sample.valid) {
            return;
        }

        if (release_candidate_) {
            if (sample.down) {
                // A short up/down excursion is contact bounce. Keep the
                // original press timestamp, displacement, and fired flags.
                release_candidate_ = false;
                release_samples_ = 0;
            } else {
                ++release_samples_;
                if (release_samples_ < kReleaseDebounceSamples) {
                    return;
                }
                const int64_t release_ms = release_started_ms_;
                release_candidate_ = false;
                release_samples_ = 0;
                FinishRelease(release_ms);
                return;
            }
        }

        // Evaluate the double-tap deadline only after a pending release has
        // been confirmed. This lets the first and second taps use the actual
        // first-up timestamp even when release debounce spans the deadline.
        FlushPendingSingle(sample.timestamp_ms);

        if (sample.down) {
            if (!pressed_) {
                BeginContact(sample);
                return;
            }

            UpdateDisplacement(sample);
            const int dx = sample.x - start_x_;
            const int dy = sample.y - start_y_;
            const int abs_dx = std::abs(dx);
            const int abs_dy = std::abs(dy);

            if (!swipe_fired_ && abs_dx > kSwipeMinHorizontalPx &&
                abs_dy <= kSwipeMaxVerticalPx && abs_dx > abs_dy) {
                CompletePendingFirstTap();
                swipe_fired_ = true;
                Emit(Gesture::kLaugh);
                return;
            }

            if (!long_press_fired_ &&
                sample.timestamp_ms - press_start_ms_ >= kLongPressMinDurationMs &&
                max_dx_ <= kTapMaxDisplacementPx && max_dy_ <= kTapMaxDisplacementPx) {
                CompletePendingFirstTap();
                long_press_fired_ = true;
                Emit(Gesture::kAnnoyed);
                return;
            }

            // A second contact that moves too far can no longer be a double
            // tap. Release the first tap now so it cannot be swallowed.
            if (second_tap_ && !swipe_fired_ &&
                (max_dx_ > kTapMaxDisplacementPx || max_dy_ > kTapMaxDisplacementPx)) {
                CompletePendingFirstTap();
                second_tap_ = false;
            }
            return;
        }

        if (pressed_) {
            release_candidate_ = true;
            release_samples_ = 1;
            release_started_ms_ = sample.timestamp_ms;
        }
    }

private:
    void Emit(Gesture gesture) {
        if (on_gesture_ && gesture != Gesture::kNone) {
            on_gesture_(gesture);
        }
    }

    void BeginContact(const Sample& sample) {
        pressed_ = true;
        press_start_ms_ = sample.timestamp_ms;
        start_x_ = sample.x;
        start_y_ = sample.y;
        max_dx_ = 0;
        max_dy_ = 0;
        swipe_fired_ = false;
        long_press_fired_ = false;
        second_tap_ = waiting_for_double_ &&
                      sample.timestamp_ms - first_release_ms_ <= kDoubleTapWindowMs;
        if (!second_tap_) {
            waiting_for_double_ = false;
        }
        // 按下瞬间的即时反馈：不等 500ms 双击窗口。第二次按下同样通知，
        // 由调用方决定是否重复播放声音（工单2 要求不叠加首触声音）。
        // 注册了 on_contact 时只走它，避免同一次按下被投递两次。
        if (on_contact_) {
            on_contact_(second_tap_);
        } else {
            Emit(Gesture::kContact);
        }
    }

    void UpdateDisplacement(const Sample& sample) {
        max_dx_ = std::max(max_dx_, std::abs(sample.x - start_x_));
        max_dy_ = std::max(max_dy_, std::abs(sample.y - start_y_));
    }

    void FinishRelease(int64_t release_ms) {
        if (!pressed_) {
            return;
        }
        pressed_ = false;
        const int64_t duration_ms = release_ms - press_start_ms_;
        const bool is_tap = !swipe_fired_ && !long_press_fired_ &&
                            duration_ms >= 0 && duration_ms < kTapMaxDurationMs &&
                            max_dx_ <= kTapMaxDisplacementPx &&
                            max_dy_ <= kTapMaxDisplacementPx;

        if (second_tap_) {
            if (is_tap && waiting_for_double_ &&
                release_ms - first_release_ms_ <= kDoubleTapWindowMs) {
                Emit(Gesture::kSurprised);
            } else {
                CompletePendingFirstTap();
            }
            second_tap_ = false;
            waiting_for_double_ = false;
        } else if (is_tap) {
            waiting_for_double_ = true;
            first_release_ms_ = release_ms;
        }
    }

    void CompletePendingFirstTap() {
        if (waiting_for_double_) {
            Emit(Gesture::kHappy);
            waiting_for_double_ = false;
        }
    }

    void FlushPendingSingle(int64_t now_ms) {
        if (waiting_for_double_ && now_ms - first_release_ms_ > kDoubleTapWindowMs) {
            CompletePendingFirstTap();
            second_tap_ = false;
        }
    }

    std::function<void(Gesture)> on_gesture_;
    std::function<void(bool)> on_contact_;
    bool pressed_ = false;
    bool release_candidate_ = false;
    int release_samples_ = 0;
    bool waiting_for_double_ = false;
    bool second_tap_ = false;
    bool swipe_fired_ = false;
    bool long_press_fired_ = false;
    int64_t press_start_ms_ = 0;
    int64_t release_started_ms_ = 0;
    int64_t first_release_ms_ = 0;
    int start_x_ = 0;
    int start_y_ = 0;
    int max_dx_ = 0;
    int max_dy_ = 0;
};

}  // namespace lckfb_touch
