#include <cassert>
#include <string>
#include <vector>

#include "../../main/boards/lckfb/szpi-esp32s3/touch_feedback.h"
#include "../../main/boards/lckfb/szpi-esp32s3/touch_gesture.h"

using lckfb_touch::Gesture;
using lckfb_touch::Recognizer;
using lckfb_touch::Sample;
using lckfb_touch::TouchSound;

static Sample Down(int64_t time_ms, int x = 100, int y = 100) {
    return {true, true, x, y, time_ms};
}

static Sample Up(int64_t time_ms) { return {true, false, 0, 0, time_ms}; }

static Sample Invalid(int64_t time_ms) { return {false, false, 0, 0, time_ms}; }

static void Expect(const std::vector<Gesture>& actual,
                   std::initializer_list<Gesture> expected) {
    assert(actual == std::vector<Gesture>(expected));
}

int main() {
    std::vector<Gesture> events;
    Recognizer recognizer([&events](Gesture gesture) { events.push_back(gesture); });

    // Single tap is delayed until the double-tap window closes.
    // kContact fires on the initial press, before any gesture is decided.
    recognizer.Update(Down(0));
    recognizer.Update(Up(100));
    recognizer.Update(Up(140));
    recognizer.Update(Up(640));
    Expect(events, {Gesture::kContact, Gesture::kHappy});
    events.clear();

    // Two valid taps inside 500 ms produce one surprise.
    recognizer.Update(Down(1000));
    recognizer.Update(Up(1100));
    recognizer.Update(Up(1140));
    recognizer.Update(Down(1300));
    recognizer.Update(Up(1400));
    recognizer.Update(Up(1440));
    Expect(events, {Gesture::kContact, Gesture::kContact, Gesture::kSurprised});
    events.clear();

    // Long press requires both duration and a stable position.
    recognizer.Update(Down(2000));
    recognizer.Update(Down(3200));
    Expect(events, {Gesture::kContact, Gesture::kAnnoyed});
    recognizer.Update(Up(3250));
    recognizer.Update(Up(3290));
    events.clear();

    // A short up/down bounce after a long press is still the same contact;
    // the already-fired long-press gesture must not fire a second time.
    recognizer.Reset();
    recognizer.Update(Down(0));
    recognizer.Update(Down(1200));
    recognizer.Update(Up(1240));
    recognizer.Update(Down(1280));
    recognizer.Update(Down(2480));
    Expect(events, {Gesture::kContact, Gesture::kAnnoyed});
    events.clear();

    // Release debounce must not turn a valid double tap into two singles.
    recognizer.Reset();
    recognizer.Update(Down(0));
    recognizer.Update(Up(80));
    recognizer.Update(Up(120));
    recognizer.Update(Down(400));
    recognizer.Update(Up(560));
    recognizer.Update(Up(600));
    recognizer.Update(Up(1080));
    Expect(events, {Gesture::kContact, Gesture::kContact, Gesture::kSurprised});
    events.clear();

    // Exactly 500 ms from the first release is still inside the double-tap
    // window; only a later timestamp may finalize the first tap.
    recognizer.Reset();
    recognizer.Update(Down(0));
    recognizer.Update(Up(80));
    recognizer.Update(Up(120));
    recognizer.Update(Down(400));
    recognizer.Update(Up(580));
    recognizer.Update(Up(620));
    recognizer.Update(Up(1120));
    Expect(events, {Gesture::kContact, Gesture::kContact, Gesture::kSurprised});
    events.clear();

    // Horizontal movement over 40 px fires exactly once.
    recognizer.Update(Down(4000));
    recognizer.Update(Down(4080, 141, 100));
    recognizer.Update(Down(4120, 180, 100));
    Expect(events, {Gesture::kContact, Gesture::kLaugh});
    recognizer.Update(Up(4160));
    recognizer.Update(Up(4200));
    events.clear();

    // Invalid reads never turn a contact into a release.
    recognizer.Update(Down(5000));
    recognizer.Update(Invalid(5040));
    recognizer.Update(Down(5080));
    recognizer.Update(Up(5100));
    recognizer.Update(Up(5140));
    recognizer.Update(Up(5640));
    Expect(events, {Gesture::kContact, Gesture::kHappy});
    events.clear();

    // A second long press must not swallow the first valid tap.
    recognizer.Update(Down(6000));
    recognizer.Update(Up(6100));
    recognizer.Update(Up(6140));
    recognizer.Update(Down(6300));
    recognizer.Update(Down(7500));
    Expect(events,
           {Gesture::kContact, Gesture::kContact, Gesture::kHappy, Gesture::kAnnoyed});
    events.clear();

    // Contact callback reports whether this press is the second tap of a pair,
    // so the board can skip replaying the first-contact sound.
    std::vector<Gesture> callback_events;
    std::vector<bool> contact_flags;
    Recognizer with_contact(
        [&callback_events](Gesture gesture) { callback_events.push_back(gesture); },
        [&contact_flags](bool second) { contact_flags.push_back(second); });
    with_contact.Update(Down(0));
    with_contact.Update(Up(80));
    with_contact.Update(Up(120));
    with_contact.Update(Down(300));
    with_contact.Update(Up(360));
    with_contact.Update(Up(400));
    assert(contact_flags == std::vector<bool>({false, true}));
    // Gesture callback must not receive kContact when on_contact is registered.
    for (Gesture gesture : callback_events) {
        assert(gesture != Gesture::kContact);
    }

    // Feedback table: gesture -> emotion + sound request.
    auto contact_first = lckfb_touch::ResolveFeedback(Gesture::kContact, false);
    assert(contact_first.sound == TouchSound::kContact);
    assert(std::string(contact_first.emotion) == "surprised");

    auto contact_second = lckfb_touch::ResolveFeedback(Gesture::kContact, true);
    assert(contact_second.sound == TouchSound::kNone);
    assert(contact_second.emotion == nullptr);

    auto single = lckfb_touch::ResolveFeedback(Gesture::kHappy, false);
    assert(single.sound == TouchSound::kNone);
    assert(std::string(single.emotion) == "surprised");

    auto double_tap = lckfb_touch::ResolveFeedback(Gesture::kSurprised, false);
    assert(double_tap.sound == TouchSound::kDoubleTap);
    assert(std::string(double_tap.emotion) == "laugh");

    auto long_press = lckfb_touch::ResolveFeedback(Gesture::kAnnoyed, false);
    assert(long_press.sound == TouchSound::kLongPress);
    assert(std::string(long_press.emotion) == "happy");

    auto swipe = lckfb_touch::ResolveFeedback(Gesture::kLaugh, false);
    assert(swipe.sound == TouchSound::kSwipe);
    assert(std::string(swipe.emotion) == "pout");

    auto none = lckfb_touch::ResolveFeedback(Gesture::kNone, false);
    assert(none.sound == TouchSound::kNone);
    assert(none.emotion == nullptr);

    return 0;
}
