#include <cassert>

#include "../../main/audio/ui_sound_arbiter.h"

int main() {
    UiSoundArbiter arbiter;

    // 1. TTS 会话忙：首包未到、队列为空也拒绝本地音效。
    assert(arbiter.TryStart() != 0);  // 空闲可起一段
    arbiter.SetTtsBusy(true);         // 进入 TTS 会话 → 作废在途
    assert(!arbiter.Active());
    assert(arbiter.TryStart() == 0);  // 会话期间拒绝
    arbiter.SetTtsBusy(false);
    assert(arbiter.TryStart() != 0);  // 会话结束可再起
    arbiter.Cancel();

    // 2. 代次令牌：TTS 入站作废令牌、生产者停止。
    const uint32_t gen = arbiter.TryStart();
    assert(gen != 0);
    assert(arbiter.IsCurrent(gen));
    assert(arbiter.OnTtsIngress());   // 需清队列
    assert(!arbiter.IsCurrent(gen));  // 旧令牌已作废

    // 3. “暂时无帧”不算结束：生产未结束时排空不收敛。
    const uint32_t gen2 = arbiter.TryStart();
    assert(gen2 != 0);
    assert(!arbiter.OnPlaybackDrained());  // 仍在生产 → 不收敛
    assert(arbiter.Active());
    arbiter.SetProducing(false);           // 生产结束
    assert(arbiter.OnPlaybackDrained());   // 现在才真正结束
    assert(!arbiter.Active());

    // 4. 静音丢弃后的状态收敛：恢复后能再次播放。
    const uint32_t gen3 = arbiter.TryStart();
    assert(gen3 != 0);
    arbiter.SetMuted(true);            // 静音 → 作废在途
    assert(!arbiter.IsCurrent(gen3));
    assert(!arbiter.Active());
    assert(arbiter.TryStart() == 0);   // 静音期间拒绝
    arbiter.SetMuted(false);
    assert(arbiter.TryStart() != 0);   // 恢复后可再起

    // 5. 已有在途时不允许再起一段。
    assert(arbiter.TryStart() == 0);

    return 0;
}
