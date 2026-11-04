#include "emote_display.h"

// Standard C++ headers
#include <algorithm>
#include <cinttypes>
#include <cstdio>
#include <cstring>
#include <memory>
#include <tuple>
#include <unordered_map>

// Standard C headers
#include <sys/time.h>
#include <time.h>

// ESP-IDF headers
#include <esp_lcd_panel_io.h>
#include <esp_log.h>
#include <esp_timer.h>
#include <lvgl.h>

// FreeRTOS headers
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

// Project headers
#include "assets.h"
#include "assets/lang_config.h"
#include "board.h"
#include "expression_emote.h"
#include "gfx.h"

namespace emote {

// ============================================================================
// Constants and Type Definitions
// ============================================================================

static const char* TAG = "EmoteDisplay";

// ============================================================================
// Forward Declarations
// ============================================================================

class EmoteDisplay;

// ============================================================================
// Helper Functions
// ============================================================================

static bool OnFlushIoReady(const esp_lcd_panel_io_handle_t panel_io,
                           esp_lcd_panel_io_event_data_t* const edata, void* user_ctx) {
    emote_handle_t handle = static_cast<emote_handle_t>(user_ctx);
    if (handle) {
        emote_notify_flush_finished(handle);
    }
    return true;
}

// Flush callback for emote
static void OnFlushCallback(int x_start, int y_start, int x_end, int y_end, const void* data,
                            emote_handle_t handle) {
    esp_lcd_panel_handle_t panel = (esp_lcd_panel_handle_t)emote_get_user_data(handle);
    if (panel != nullptr) {
        esp_lcd_panel_draw_bitmap(panel, x_start, y_start, x_end, y_end, data);
    }
}

// ============================================================================
// Graphics Initialization Functions
// ============================================================================

static emote_handle_t InitializeEmote(const esp_lcd_panel_handle_t panel, const int width,
                                      const int height) {
    if (!panel) {
        ESP_LOGE(TAG, "Invalid panel");
        return nullptr;
    }

    emote_config_t emote_cfg = {
        .flags =
            {
                .swap = true,
                .double_buffer = true,
                .buff_dma = false,
            },
        .gfx_emote =
            {
                .h_res = width,
                .v_res = height,
                .fps = 30,
            },
        .buffers =
            {
                .buf_pixels = static_cast<size_t>(width * 16),
            },
        .task =
            {
                .task_priority = 5,
                .task_stack = 6 * 1024,
                .task_affinity = 0,
                .task_stack_in_ext = false,
            },
        .flush_cb = OnFlushCallback,
        .user_data = (void*)panel,
    };

    emote_handle_t emote_handle = emote_init(&emote_cfg);
    if (!emote_handle) {
        ESP_LOGE(TAG, "Failed to initialize emote");
        return nullptr;
    }

    return emote_handle;
}

// ============================================================================
// EmoteDisplay Class Implementation
// ============================================================================

EmoteDisplay::EmoteDisplay(const esp_lcd_panel_handle_t panel,
                           const esp_lcd_panel_io_handle_t panel_io, const int width,
                           const int height) {
    emote_handle_ = InitializeEmote(panel, width, height);

    const esp_lcd_panel_io_callbacks_t cbs = {
        .on_color_trans_done = OnFlushIoReady,
    };
    esp_lcd_panel_io_register_event_callbacks(panel_io, &cbs, emote_handle_);
}

EmoteDisplay::~EmoteDisplay() {
    if (emote_handle_) {
        emote_deinit(emote_handle_);
        emote_handle_ = nullptr;
    }
}

void EmoteDisplay::SetEmotion(const char* const emotion) {
    ESP_LOGI(TAG, "SetEmotion: %s", emotion);
    if (emote_handle_ && emotion && strlen(emotion) > 0) {
        emote_set_anim_emoji(emote_handle_, emotion);
        RefreshBatteryOverlay();
    }
}

void EmoteDisplay::RefreshBatteryOverlay() {
    if (emote_handle_ == nullptr) {
        return;
    }

    gfx_obj_t* label = emote_get_obj_by_name(emote_handle_, "battery_label");
    if (label == nullptr) {
        return;
    }

    if (emote_lock(emote_handle_) != ESP_OK) {
        return;
    }

    if (!battery_valid_) {
        gfx_label_set_text(label, "");
        gfx_obj_set_visible(label, false);
        emote_unlock(emote_handle_);
        return;
    }

    char text[8];
    std::snprintf(text, sizeof(text), "%d%%", battery_level_);
    gfx_label_set_text(label, text);
    gfx_label_set_color(label, GFX_COLOR_HEX(0xB8D8E8));
    gfx_label_set_opa(label, 160);
    gfx_obj_set_visible(label, true);
    emote_unlock(emote_handle_);
}

void EmoteDisplay::SetBatteryLevel(const int level, const bool charging) {
    const bool valid = level >= 0 && level <= 100;

    // A valid value supplied through this public hook is an external value.
    // Keep it across periodic board polling when the board has no sampler.
    battery_override_ = valid;
    battery_valid_ = valid;
    battery_level_ = valid ? level : -1;
    battery_charging_ = valid && charging;

    if (emote_handle_ == nullptr) {
        return;
    }

    if (!valid) {
        // Do not send an invalid BAT event: esp_emote_expression clamps a
        // negative percentage to 0, which would display a false "0%".
        RefreshBatteryOverlay();
        return;
    }

    // Keep the expression manager's battery cache in sync for future idle
    // events. The custom layout intentionally has no battery/status icons.
    char event_msg[16];
    std::snprintf(event_msg, sizeof(event_msg), "%d,%d", battery_charging_ ? 1 : 0,
                  battery_level_);
    emote_set_event_msg(emote_handle_, EMOTE_MGR_EVT_BAT, event_msg);
    RefreshBatteryOverlay();
}

void EmoteDisplay::SetChatMessage(const char* const role, const char* const content) {
    ESP_LOGI(TAG, "SetChatMessage: %s, %s", role, content);
    if (emote_handle_ && content && strlen(content) > 0) {
        if ((std::strcmp(role, "system") == 0) && std::strstr(content, "xiaozhi.me")) {
            size_t len = strlen(content);
            char* new_content = new char[len + 1];
            strcpy(new_content, content);
            std::replace(new_content, new_content + len, static_cast<char>(0x0A),
                         static_cast<char>(0x20));
            emote_set_event_msg(emote_handle_, EMOTE_MGR_EVT_SYS, new_content);
            delete[] new_content;
        } else {
            emote_set_event_msg(emote_handle_, EMOTE_MGR_EVT_SPEAK, content);
        }
    }
    RefreshBatteryOverlay();
}

void EmoteDisplay::SetStatus(const char* const status) {
    ESP_LOGI(TAG, "SetStatus: %s", status);
    if (emote_handle_ && status && strlen(status) > 0) {
        if (std::strcmp(status, Lang::Strings::LISTENING) == 0) {
            emote_set_event_msg(emote_handle_, EMOTE_MGR_EVT_LISTEN, NULL);
        } else if (std::strcmp(status, Lang::Strings::STANDBY) == 0) {
            emote_set_event_msg(emote_handle_, EMOTE_MGR_EVT_IDLE, NULL);
        } else if (std::strcmp(status, Lang::Strings::SPEAKING) == 0) {
            emote_set_event_msg(emote_handle_, EMOTE_MGR_EVT_SPEAK, NULL);
        } else if (std::strcmp(status, Lang::Strings::ERROR) == 0) {
            emote_set_event_msg(emote_handle_, EMOTE_MGR_EVT_SET, NULL);
        }
    }
    RefreshBatteryOverlay();
}

void EmoteDisplay::ShowNotification(const char* notification, int duration_ms) {
    ESP_LOGI(TAG, "ShowNotification: %s", notification);
    if (emote_handle_ && notification && strlen(notification) > 0) {
        emote_set_event_msg(emote_handle_, EMOTE_MGR_EVT_SYS, notification);
    }
    RefreshBatteryOverlay();
}

void EmoteDisplay::UpdateStatusBar(bool update_all) {
    ESP_LOGD(TAG, "UpdateStatusBar: %s", update_all ? "true" : "false");
    if (!emote_handle_) {
        return;
    }

    int level = -1;
    bool charging = false;
    bool discharging = false;
    const bool board_battery_valid =
        Board::GetInstance().GetBatteryLevel(level, charging, discharging) && level >= 0 &&
        level <= 100;
    if (board_battery_valid) {
        SetBatteryLevel(level, charging);
        // The value came from the board sampler, not the external hook.
        battery_override_ = false;
    } else if (!battery_override_) {
        SetBatteryLevel(-1, false);
    } else {
        // Keep a valid value supplied by a future external battery event when
        // this board has no ADC-backed GetBatteryLevel implementation.
        RefreshBatteryOverlay();
    }
}

void EmoteDisplay::SetPowerSaveMode(bool on) {
    ESP_LOGI(TAG, "SetPowerSaveMode: %s", on ? "ON" : "OFF");
    if (!emote_handle_) {
        return;
    }
}

void EmoteDisplay::SetPreviewImage(const void* image) {
    if (image) {
        ESP_LOGI(TAG, "SetPreviewImage: Preview image not supported, using default icon");
    }
}

bool EmoteDisplay::MountAssets(const char* partition_label) {
    if (emote_handle_ == nullptr || partition_label == nullptr) {
        return false;
    }
    const emote_data_t data = {
        .type = EMOTE_SOURCE_PARTITION,
        .source =
            {
                .partition_label = partition_label,
            },
        .flags =
            {
                .mmap_enable = true,
            },
    };
    return emote_mount_assets(emote_handle_, &data) == ESP_OK;
}

void EmoteDisplay::UnmountAssets() {
    if (emote_handle_ != nullptr) {
        emote_unmount_assets(emote_handle_);
    }
}

bool EmoteDisplay::GetAssetData(const std::string& name, const uint8_t*& data, size_t& size) {
    if (emote_handle_ == nullptr) {
        return false;
    }
    return emote_get_asset_data_by_name(emote_handle_, name.c_str(), &data, &size) == ESP_OK;
}

void EmoteDisplay::LoadAssets() {
    if (emote_handle_ != nullptr) {
        emote_load_assets(emote_handle_);
        // The expression manager initializes its BAT state to 0. Hide the
        // overlay until a real or externally supplied value arrives.
        battery_level_ = -1;
        battery_charging_ = false;
        battery_valid_ = false;
        battery_override_ = false;
        RefreshBatteryOverlay();
    }
}

void EmoteDisplay::SetTheme(Theme* const theme) { ESP_LOGI(TAG, "SetTheme: %p", theme); }

bool EmoteDisplay::Lock(const int timeout_ms) {
    (void)timeout_ms;
    return true;
}

void EmoteDisplay::Unlock() {}

bool EmoteDisplay::StopAnimDialog() {
    ESP_LOGI(TAG, "StopAnimDialog");
    if (emote_handle_) {
        return emote_stop_anim_dialog(emote_handle_);
    }
    return false;
}

bool EmoteDisplay::InsertAnimDialog(const char* emoji_name, uint32_t duration_ms) {
    ESP_LOGI(TAG, "InsertAnimDialog: %s, %" PRIu32, emoji_name, duration_ms);
    if (emote_handle_ && emoji_name) {
        return emote_insert_anim_dialog(emote_handle_, emoji_name, duration_ms);
    }
    return false;
}

void EmoteDisplay::RefreshAll() {
    if (emote_handle_) {
        emote_notify_all_refresh(emote_handle_);
        return;
    }
}

}  // namespace emote
