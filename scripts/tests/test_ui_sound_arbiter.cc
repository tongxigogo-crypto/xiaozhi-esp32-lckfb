#include <atomic>
#include <cassert>
#include <thread>

#include "../../main/audio/ui_sound_arbiter.h"

int main() {
    UiSoundArbiter arbiter;

    // 1. TTS 会话忙：首包未到、队列为空也拒绝本地音效。
    assert(arbiter.TryStart() != 0);
    arbiter.SetTtsBusy(true);   // 进入 TTS 会话 → 作废在途
    assert(!arbiter.Active());
    assert(arbiter.TryStart() == 0);
    arbiter.SetTtsBusy(false);
    assert(arbiter.TryStart() != 0);
    arbiter.Cancel();

    // 2. 代次令牌：TTS 入站作废令牌、生产者停止。
    const uint32_t gen = arbiter.TryStart();
    assert(gen != 0);
    assert(arbiter.IsCurrent(gen));
    assert(arbiter.OnTtsIngress());
    assert(!arbiter.IsCurrent(gen));

    // 3. 「排空先发生、生产后结束」必须收敛，而不是卡住占用。
    const uint32_t a = arbiter.TryStart();
    assert(a != 0);
    assert(!arbiter.OnPlaybackDrained());  // 仍在生产，不收敛
    assert(arbiter.Active());
    arbiter.EndProducing(a);               // 生产后结束
    assert(arbiter.OnPlaybackDrained());   // 现在真正结束
    assert(!arbiter.Active());
    assert(arbiter.TryStart() != 0);       // 恢复后能再起
    arbiter.Cancel();

    // 4. 旧段迟到地结束，不得清掉新段的生产状态。
    const uint32_t old_gen = arbiter.TryStart();
    assert(old_gen != 0);
    arbiter.Cancel();                       // 作废旧段
    const uint32_t new_gen = arbiter.TryStart();
    assert(new_gen != 0);
    arbiter.EndProducing(old_gen);          // 旧任务迟到结束
    assert(arbiter.Producing());            // 新段仍在生产
    assert(!arbiter.OnPlaybackDrained());   // 仍生产 → 不收敛
    arbiter.EndProducing(new_gen);
    assert(arbiter.OnPlaybackDrained());
    assert(!arbiter.Active());

    // 5. 静音丢弃后的状态收敛：恢复后能再次播放。
    const uint32_t b = arbiter.TryStart();
    assert(b != 0);
    arbiter.SetMuted(true);
    assert(!arbiter.IsCurrent(b));
    assert(!arbiter.Active());
    assert(arbiter.TryStart() == 0);   // 静音期间拒绝
    arbiter.SetMuted(false);
    assert(arbiter.TryStart() != 0);   // 恢复后可再起

    // 6. 已有在途时不允许再起一段。
    assert(arbiter.TryStart() == 0);

    // 7. 并发回归：旧生产者在取消后迟到结束，不得清掉新段的生产状态。
    // 受控双线程，多轮压测：TryStart 在子线程、Cancel+TryStart 在主线程，
    // 旧段 EndProducing(old_gen) 必须 CAS 失败，新段 producing 保持不变。
    for (int i = 0; i < 5000; ++i) {
        UiSoundArbiter race;
        std::atomic<uint32_t> old_gen{0};
        std::atomic<bool> ready{false};
        std::thread producer([&]() {
            old_gen.store(race.TryStart(), std::memory_order_release);
            ready.store(true, std::memory_order_release);
            // 模拟“生产结束”发生在取消之后。
            while (ready.load(std::memory_order_acquire)) {
            }
            race.EndProducing(old_gen.load(std::memory_order_relaxed));
        });
        while (!ready.load(std::memory_order_acquire)) {
        }
        race.Cancel();
        const uint32_t new_gen = race.TryStart();
        assert(new_gen != 0);
        ready.store(false, std::memory_order_release);
        producer.join();
        assert(race.IsCurrent(new_gen));
        assert(race.Producing());
    }

    return 0;
}
