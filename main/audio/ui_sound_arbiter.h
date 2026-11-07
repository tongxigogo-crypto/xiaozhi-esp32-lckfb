#pragma once

#include <atomic>
#include <cstdint>

// 本地触摸音效的播放权仲裁。纯逻辑、无 FreeRTOS 依赖，可离线单测。
//
// 规则（工单2 §6.4）：显式静音 > TTS 会话 > 本地触摸音效。
// 关键语义：
//   - TTS「忙」是一个会话级状态（SetTtsBusy），不是「队列此刻非空」——
//     TTS 首包未到、包间空隙，通道仍归 TTS，本地音效不得抢入。
//   - 每段本地音效持有一个代次令牌；TTS 入站即作废令牌并停止生产。
//   - 「队列暂时为空」不等于「整段结束」：只有生产结束且已排空才收敛。
class UiSoundArbiter {
public:
    // 显式静音（服务端“安静”锁存）。置真立即作废在途。
    void SetMuted(bool muted) {
        if (muted) {
            Cancel();
        }
        muted_.store(muted, std::memory_order_release);
    }
    bool Muted() const { return muted_.load(std::memory_order_acquire); }

    // TTS 会话开始/结束。进入即作废在途本地音效。
    void SetTtsBusy(bool busy) {
        if (busy) {
            Cancel();
        }
        tts_busy_.store(busy, std::memory_order_release);
    }
    bool TtsBusy() const { return tts_busy_.load(std::memory_order_acquire); }

    // 尝试开始一段本地音效。返回 0 表示被拒绝（静音 / TTS 忙 / 已有在途）。
    uint32_t TryStart() {
        if (Muted() || TtsBusy()) {
            return 0;
        }
        bool expected = false;
        if (!active_.compare_exchange_strong(expected, true)) {
            return 0;
        }
        producing_.store(true, std::memory_order_release);
        return generation_.fetch_add(1, std::memory_order_acq_rel) + 1;
    }

    // 代次是否仍然有效（生产者每包入队前询问）。
    bool IsCurrent(uint32_t generation) const {
        return generation != 0 && generation_.load(std::memory_order_acquire) == generation &&
               active_.load(std::memory_order_acquire);
    }

    // 生产（解复用 + 入队）结束。
    void SetProducing(bool producing) { producing_.store(producing, std::memory_order_release); }
    bool Producing() const { return producing_.load(std::memory_order_acquire); }
    bool Active() const { return active_.load(std::memory_order_acquire); }

    // TTS 包入站：若本地音效占用中，作废并返回 true（需要清队列）。
    bool OnTtsIngress() {
        if (Active() || Producing()) {
            Cancel();
            return true;
        }
        return false;
    }

    // 播放排空：仅当生产已结束且无剩余帧时，整段才算真正结束。
    bool OnPlaybackDrained() {
        if (Active() && !Producing()) {
            active_.store(false, std::memory_order_release);
            return true;
        }
        return false;
    }

    // 作废在途：令牌 +1，生产与占用同时清零。
    void Cancel() {
        generation_.fetch_add(1, std::memory_order_acq_rel);
        producing_.store(false, std::memory_order_release);
        active_.store(false, std::memory_order_release);
    }

private:
    std::atomic<bool> muted_{false};
    std::atomic<bool> tts_busy_{false};
    std::atomic<bool> active_{false};
    std::atomic<bool> producing_{false};
    std::atomic<uint32_t> generation_{0};
};
