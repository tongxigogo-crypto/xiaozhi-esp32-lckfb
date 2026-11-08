#ifndef _WEBSOCKET_PROTOCOL_H_
#define _WEBSOCKET_PROTOCOL_H_

#include "protocol.h"

#include <freertos/FreeRTOS.h>
#include <freertos/event_groups.h>
#include <web_socket.h>
#include <atomic>
#include <mutex>

#define WEBSOCKET_PROTOCOL_SERVER_HELLO_EVENT (1 << 0)
#define WEBSOCKET_PROTOCOL_OPEN_CANCEL_EVENT (1 << 1)

class WebsocketProtocol : public Protocol {
public:
    WebsocketProtocol();
    ~WebsocketProtocol();

    bool Start() override;
    bool SendAudio(std::unique_ptr<AudioStreamPacket> packet) override;
    bool OpenAudioChannel() override;
    bool OpenAudioChannelForEpoch(uint64_t reservation_epoch) override;
    void CloseAudioChannel(bool send_goodbye = true) override;
    void CancelOpenAudioChannel() override;
    bool IsAudioChannelOpened() const override;

private:
    EventGroupHandle_t event_group_handle_;
    std::shared_ptr<WebSocket> websocket_;
    mutable std::mutex websocket_mutex_;
    std::atomic<bool> open_cancelled_{false};
    std::atomic<bool> open_in_progress_{false};
    std::atomic<uint64_t> published_epoch_{0};
    int version_ = 1;

    void ParseServerHello(const cJSON* root);
    bool SendText(const std::string& text) override;
    std::string GetHelloMessage();
    void OnAudioChannelOpenReserved(uint64_t reservation_epoch) override;
};

#endif
