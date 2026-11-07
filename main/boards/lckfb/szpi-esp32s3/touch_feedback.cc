#include "touch_feedback.h"

#include <cstddef>
#include <cstdint>

// 素材由 main/assets/common/*.ogg 经 IDF EMBED_FILES 内嵌，符号名为 _binary_<文件名>_ogg_start。
#define XFY_TOUCH_CLIP(name)                                                     \
    extern const uint8_t name##_start[] asm("_binary_" #name "_ogg_start");       \
    extern const uint8_t name##_end[] asm("_binary_" #name "_ogg_end");

XFY_TOUCH_CLIP(touch_contact_xiaohe)
XFY_TOUCH_CLIP(touch_double_xiaohe)
XFY_TOUCH_CLIP(touch_long_xiaohe)
XFY_TOUCH_CLIP(touch_swipe_xiaohe)
XFY_TOUCH_CLIP(touch_contact_yunzhou)
XFY_TOUCH_CLIP(touch_double_yunzhou)
XFY_TOUCH_CLIP(touch_long_yunzhou)
XFY_TOUCH_CLIP(touch_swipe_yunzhou)

#undef XFY_TOUCH_CLIP

namespace lckfb_touch {
namespace {

std::string_view MakeClip(const uint8_t* start, const uint8_t* end) {
    return {reinterpret_cast<const char*>(start), static_cast<size_t>(end - start)};
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
                return MakeClip(touch_contact_yunzhou_start, touch_contact_yunzhou_end);
            case TouchSound::kDoubleTap:
                return MakeClip(touch_double_yunzhou_start, touch_double_yunzhou_end);
            case TouchSound::kLongPress:
                return MakeClip(touch_long_yunzhou_start, touch_long_yunzhou_end);
            case TouchSound::kSwipe:
                return MakeClip(touch_swipe_yunzhou_start, touch_swipe_yunzhou_end);
            case TouchSound::kNone:
            default:
                return {};
        }
    }
    switch (sound) {
        case TouchSound::kContact:
            return MakeClip(touch_contact_xiaohe_start, touch_contact_xiaohe_end);
        case TouchSound::kDoubleTap:
            return MakeClip(touch_double_xiaohe_start, touch_double_xiaohe_end);
        case TouchSound::kLongPress:
            return MakeClip(touch_long_xiaohe_start, touch_long_xiaohe_end);
        case TouchSound::kSwipe:
            return MakeClip(touch_swipe_xiaohe_start, touch_swipe_xiaohe_end);
        case TouchSound::kNone:
        default:
            return {};
    }
}

}  // namespace lckfb_touch
