#include <cassert>
#include <vector>

#include "../../main/boards/lckfb/szpi-esp32s3/touch_gesture.h"

using lckfb_touch::Gesture;
using lckfb_touch::Recognizer;
using lckfb_touch::Sample;

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
    recognizer.Update(Down(0));
    recognizer.Update(Up(100));
    recognizer.Update(Up(140));
    recognizer.Update(Up(640));
    Expect(events, {Gesture::kHappy});
    events.clear();

    // Two valid taps inside 500 ms produce one surprise.
    recognizer.Update(Down(1000));
    recognizer.Update(Up(1100));
    recognizer.Update(Up(1140));
    recognizer.Update(Down(1300));
    recognizer.Update(Up(1400));
    recognizer.Update(Up(1440));
    Expect(events, {Gesture::kSurprised});
    events.clear();

    // Long press requires both duration and a stable position.
    recognizer.Update(Down(2000));
    recognizer.Update(Down(3200));
    Expect(events, {Gesture::kAnnoyed});
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
    Expect(events, {Gesture::kAnnoyed});
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
    Expect(events, {Gesture::kSurprised});
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
    Expect(events, {Gesture::kSurprised});
    events.clear();

    // Horizontal movement over 40 px fires exactly once.
    recognizer.Update(Down(4000));
    recognizer.Update(Down(4080, 141, 100));
    recognizer.Update(Down(4120, 180, 100));
    Expect(events, {Gesture::kLaugh});
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
    Expect(events, {Gesture::kHappy});
    events.clear();

    // A second long press must not swallow the first valid tap.
    recognizer.Update(Down(6000));
    recognizer.Update(Up(6100));
    recognizer.Update(Up(6140));
    recognizer.Update(Down(6300));
    recognizer.Update(Down(7500));
    Expect(events, {Gesture::kHappy, Gesture::kAnnoyed});

    return 0;
}
