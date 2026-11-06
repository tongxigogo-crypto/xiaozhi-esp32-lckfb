#pragma once
#include <sys/time.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <limits>
#include <string>

namespace NetworkTime {
// A cold ESP32 clock starts at epoch zero. TLS still performs certificate
// validation; this bound only prevents attempting it before network time exists.
inline bool ClockPlausible(time_t now) { return now >= 1704067200LL && now < 4102444800LL; }
inline bool NeedsClock(const std::string& url, bool date_verification) {
    return date_verification && (url.rfind("https://", 0) == 0 || url.rfind("wss://", 0) == 0);
}
template <typename Now, typename Sleep>
bool WaitUntilReady(unsigned timeout_ms, Now now, Sleep sleep) {
    unsigned elapsed = 0;
    while (!ClockPlausible(now())) {
        if (elapsed >= timeout_ms)
            return false;
        const auto delay = std::min(100u, timeout_ms - elapsed);
        sleep(delay);
        elapsed += delay;
    }
    return true;
}
inline bool ServerTimeval(double timestamp_ms, timeval& tv) {
    if (!std::isfinite(timestamp_ms) || timestamp_ms < 1704067200000.0 ||
        timestamp_ms >= 4102444800000.0)
        return false;
    const double seconds = std::floor(timestamp_ms / 1000.0);
    if (seconds > static_cast<double>(std::numeric_limits<time_t>::max()))
        return false;
    tv.tv_sec = static_cast<time_t>(seconds);
    tv.tv_usec = static_cast<suseconds_t>(std::floor(timestamp_ms - seconds * 1000.0)) * 1000;
    return true;
}
inline std::string PosixTimezone(double minutes) {
    if (!std::isfinite(minutes) || std::trunc(minutes) != minutes || std::abs(minutes) > 14 * 60)
        return {};
    const int offset = static_cast<int>(minutes);
    char value[24];
    std::snprintf(value, sizeof(value), "UTC%c%02d:%02d", offset >= 0 ? '-' : '+',
                  std::abs(offset) / 60, std::abs(offset) % 60);
    return value;
}
void StartSync();
bool WaitForTls(const std::string& url, unsigned timeout_ms = 10000);
}  // namespace NetworkTime
