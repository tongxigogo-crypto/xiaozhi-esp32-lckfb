#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <cJSON.h>
#include <atomic>
#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <vector>

struct AudioStreamPacket {
    int sample_rate = 0;
    int frame_duration = 0;
    uint32_t timestamp = 0;
    uint32_t playback_id = 0;
    uint32_t media_position_ms = 0;
    // 本地触摸短声音专用：标记来源与所属播放代次，TTS 抢占后按代次丢弃，
    // 不会混进云端语音的播放链路（工单2 §6.4）。
    bool is_ui_sound = false;
    uint32_t ui_generation = 0;
    std::vector<uint8_t> payload;
};

struct BinaryProtocol2 {
    uint16_t version;
    uint16_t type;          // Message type (0: OPUS, 1: JSON)
    uint32_t reserved;      // Reserved for future use
    uint32_t timestamp;     // Timestamp in milliseconds (used for server-side AEC)
    uint32_t payload_size;  // Payload size in bytes
    uint8_t payload[];      // Payload data
} __attribute__((packed));

struct BinaryProtocol3 {
    uint8_t type;
    uint8_t reserved;
    uint16_t payload_size;
    uint8_t payload[];
} __attribute__((packed));

enum AbortReason { kAbortReasonNone, kAbortReasonWakeWordDetected };

enum ListeningMode {
    kListeningModeAutoStop,
    kListeningModeManualStop,
    kListeningModeRealtime  // 需要 AEC 支持
};

class Protocol {
public:
    virtual ~Protocol() = default;

    inline int server_sample_rate() const { return server_sample_rate_; }
    inline int server_frame_duration() const { return server_frame_duration_; }
    inline const std::string& session_id() const { return session_id_; }
    inline uint64_t ConnectionEpoch() const {
        return connection_epoch_.load(std::memory_order_acquire);
    }

    void OnIncomingAudio(std::function<void(std::unique_ptr<AudioStreamPacket> packet)> callback);
    void OnIncomingAudioWithEpoch(
        std::function<void(uint64_t, std::unique_ptr<AudioStreamPacket> packet)> callback);
    void OnIncomingJson(std::function<void(const cJSON* root)> callback);
    void OnIncomingJsonWithEpoch(std::function<void(uint64_t, const cJSON* root)> callback);
    void OnAudioChannelOpened(std::function<void()> callback);
    void OnAudioChannelOpenedWithEpoch(std::function<void(uint64_t)> callback);
    void OnAudioChannelClosed(std::function<void()> callback);
    void OnAudioChannelClosedWithEpoch(std::function<void(uint64_t)> callback);
    void OnNetworkError(std::function<void(const std::string& message)> callback);
    void OnConnected(std::function<void()> callback);
    void OnDisconnected(std::function<void()> callback);

    virtual bool Start() = 0;
    virtual bool OpenAudioChannel() = 0;
    // Recovery workers reserve a transport epoch on the application task before
    // they are dispatched.  A cancelled reservation must never be revived by
    // a worker that has not reached its Open call yet.
    uint64_t ReserveAudioChannelOpen();
    void CancelReservedAudioChannelOpen(uint64_t reservation_epoch);
    virtual bool OpenAudioChannelForEpoch(uint64_t reservation_epoch) = 0;
    virtual void CloseAudioChannel(bool send_goodbye = true) = 0;
    virtual void CancelOpenAudioChannel() { BeginConnectionAttempt(); }
    virtual bool IsAudioChannelOpened() const = 0;
    virtual bool SendAudio(std::unique_ptr<AudioStreamPacket> packet) = 0;
    virtual void SendWakeWordDetected(const std::string& wake_word);
    virtual void SendStartListening(ListeningMode mode);
    virtual void SendStopListening();
    virtual void SendAbortSpeaking(AbortReason reason);
    virtual void SendMcpMessage(const std::string& message);

protected:
    std::function<void(const cJSON* root)> on_incoming_json_;
    std::function<void(uint64_t, const cJSON* root)> on_incoming_json_epoch_;
    std::function<void(std::unique_ptr<AudioStreamPacket> packet)> on_incoming_audio_;
    std::function<void(uint64_t, std::unique_ptr<AudioStreamPacket> packet)>
        on_incoming_audio_epoch_;
    std::function<void()> on_audio_channel_opened_;
    std::function<void(uint64_t)> on_audio_channel_opened_epoch_;
    std::function<void()> on_audio_channel_closed_;
    std::function<void(uint64_t)> on_audio_channel_closed_epoch_;
    std::function<void(const std::string& message)> on_network_error_;
    std::function<void()> on_connected_;
    std::function<void()> on_disconnected_;

    int server_sample_rate_ = 24000;
    int server_frame_duration_ = 60;
    bool error_occurred_ = false;
    std::string session_id_;
    uint64_t BeginConnectionAttempt() { return ++connection_epoch_; }
    uint64_t connection_epoch() const { return connection_epoch_.load(std::memory_order_acquire); }
    bool IsAudioChannelOpenReservationValid(uint64_t reservation_epoch) const {
        return reservation_epoch != 0 &&
               open_reservation_epoch_.load(std::memory_order_acquire) == reservation_epoch &&
               connection_epoch() == reservation_epoch;
    }
    virtual void OnAudioChannelOpenReserved(uint64_t reservation_epoch) { (void)reservation_epoch; }
    std::chrono::time_point<std::chrono::steady_clock> last_incoming_time_;
    std::atomic<uint64_t> connection_epoch_{0};
    std::atomic<uint64_t> open_reservation_epoch_{0};

    virtual bool SendText(const std::string& text) = 0;
    virtual void SetError(const std::string& message);
    void SetError(const std::string& message, const std::string& detail);
    virtual bool IsTimeout() const;
    static void AddTextFontCapabilities(cJSON* root);
};

#endif  // PROTOCOL_H
