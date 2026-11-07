#pragma once

#include "touch_gesture.h"

namespace lckfb_touch {

// 本地短声音类别。素材未接入前只在日志里记录请求，不出声（工单2 §6.3）。
enum class TouchSound {
    kNone,
    kContact,
    kDoubleTap,
    kLongPress,
    kSwipe,
};

const char* TouchSoundName(TouchSound sound);

struct TouchFeedback {
    const char* emotion;  // nullptr 表示不改表情
    TouchSound sound;
};

// 手势 → 表情与声音的唯一映射点（工单2 §6.2 表）。
// 枚举名是历史包袱：kHappy=单击、kSurprised=双击、kAnnoyed=长按、kLaugh=横划。
TouchFeedback ResolveFeedback(Gesture gesture, bool second_tap);

}  // namespace lckfb_touch
