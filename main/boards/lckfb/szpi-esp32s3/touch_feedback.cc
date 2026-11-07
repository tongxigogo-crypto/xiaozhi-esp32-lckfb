#include "touch_feedback.h"

#include <cstddef>
#include <cstdint>

#include "../../../assets/touch_clips/touch_clips.h"

namespace lckfb_touch {
namespace {

template <std::size_t N>
std::string_view MakeClip(const std::uint8_t (&data)[N]) {
    return {reinterpret_cast<const char*>(data), N};
}

}  // namespace

const char* TouchSoundName(TouchSound sound) {
    switch (sound) {
        case TouchSound::kContact:
            return "contact";
        case TouchSound::kDoubleTap:
            return "double_tap";
        case TouchSound::kLongPress:
            return "long_press";
        case TouchSound::kSwipe:
            return "swipe";
        case TouchSound::kNone:
        default:
            return "none";
    }
}

TouchFeedback ResolveFeedback(Gesture gesture, bool second_tap) {
    switch (gesture) {
        case Gesture::kContact:
            // 按下即反馈；第二次按下不再叠加首触声音（工单2 §6.2）。
            return {second_tap ? nullptr : "surprised",
                    second_tap ? TouchSound::kNone : TouchSound::kContact};
        case Gesture::kHappy:
            // 单击确认：保留按下时的惊讶，不重复播长句。
            return {"surprised", TouchSound::kNone};
        case Gesture::kSurprised:
            // 双击：大笑 + 一次短回应。
            return {"laugh", TouchSound::kDoubleTap};
        case Gesture::kAnnoyed:
            // 长按原本错误地绑定烦躁，工单2 纠偏为摸头笑。
            return {"happy", TouchSound::kLongPress};
        case Gesture::kLaugh:
            // 横划原本错误地绑定大笑，工单2 纠偏为嘟嘴抗议。
            return {"pout", TouchSound::kSwipe};
        case Gesture::kNone:
        default:
            return {nullptr, TouchSound::kNone};
    }
}

std::string_view ResolveSoundClip(TouchSound sound, bool use_yunzhou) {
    if (use_yunzhou) {
        switch (sound) {
            case TouchSound::kContact:
                return MakeClip(clips::kTouchContactYunzhou);
            case TouchSound::kDoubleTap:
                return MakeClip(clips::kTouchDoubleYunzhou);
            case TouchSound::kLongPress:
                return MakeClip(clips::kTouchLongYunzhou);
            case TouchSound::kSwipe:
                return MakeClip(clips::kTouchSwipeYunzhou);
            case TouchSound::kNone:
            default:
                return {};
        }
    }
    switch (sound) {
        case TouchSound::kContact:
            return MakeClip(clips::kTouchContactXiaohe);
        case TouchSound::kDoubleTap:
            return MakeClip(clips::kTouchDoubleXiaohe);
        case TouchSound::kLongPress:
            return MakeClip(clips::kTouchLongXiaohe);
        case TouchSound::kSwipe:
            return MakeClip(clips::kTouchSwipeXiaohe);
        case TouchSound::kNone:
        default:
            return {};
    }
}

}  // namespace lckfb_touch
