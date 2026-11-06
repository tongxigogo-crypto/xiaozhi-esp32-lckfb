#include "network_time.h"
#include "sdkconfig.h"
#if CONFIG_MBEDTLS_HAVE_TIME_DATE
#include <esp_log.h>
#include <esp_netif_sntp.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <mutex>
#endif

namespace NetworkTime {
void StartSync() {
#if CONFIG_MBEDTLS_HAVE_TIME_DATE
    // Called on the WiFi event task: initialize/restart only; never wait here.
    static std::mutex mutex;
    static bool initialized = false;
    std::lock_guard<std::mutex> guard(mutex);
    if (initialized) {
        esp_netif_sntp_start();
        return;
    }
    esp_sntp_config_t config = ESP_NETIF_SNTP_DEFAULT_CONFIG("ntp.aliyun.com");
#if CONFIG_LWIP_SNTP_MAX_SERVERS > 1
    config.servers[1] = "time.cloudflare.com";
    config.num_of_servers = 2;
#endif
    const auto result = esp_netif_sntp_init(&config);
    initialized = result == ESP_OK;
    if (!initialized) {
        ESP_LOGE("NetworkTime", "SNTP initialization failed: %d", result);
    } else {
        ESP_LOGI("NetworkTime", "SNTP synchronization initialized");
    }
#endif
}
bool WaitForTls(const std::string& url, unsigned timeout_ms) {
#if CONFIG_MBEDTLS_HAVE_TIME_DATE
    if (!NeedsClock(url, true))
        return true;
    // Activation/upgrade task only. Audio and the application loop keep running.
    ESP_LOGI("NetworkTime", "TLS clock gate waiting for valid network time");
    const bool ready = WaitUntilReady(
        timeout_ms, [] { return std::time(nullptr); },
        [](unsigned ms) { vTaskDelay(pdMS_TO_TICKS(ms)); });
    if (!ready) {
        ESP_LOGW("NetworkTime", "TLS deferred: network time not ready");
    } else {
        ESP_LOGI("NetworkTime", "TLS clock ready: epoch=%lld",
                 static_cast<long long>(std::time(nullptr)));
    }
    return ready;
#else
    (void)url;
    (void)timeout_ms;
    return true;
#endif
}
}  // namespace NetworkTime
