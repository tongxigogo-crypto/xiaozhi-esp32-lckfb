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
#include "expression_emote/emote_assets.h"
#include "gfx.h"
#include "widget/gfx_font_lvgl.h"

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
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    if (emote_handle_) {
        emote_deinit(emote_handle_);
        emote_handle_ = nullptr;
    }
    if (interaction_font_) {
        gfx_font_lv_delete(interaction_font_);
        interaction_font_ = nullptr;
    }
}

void EmoteDisplay::SetEmotion(const char* const emotion) {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    ESP_LOGI(TAG, "SetEmotion: %s", emotion ? emotion : "");
    if (emote_handle_ && assets_loaded_ && emotion && strlen(emotion) > 0) {
        const char* animation = emotion;
        // Application requests "neutral" immediately after setting listening
        // or idle status. In the clean layout keep the matching state animation.
        if (std::strcmp(emotion, "neutral") == 0 && assets_loaded_ &&
            emote_lock(emote_handle_) == ESP_OK) {
            const bool clean_layout =
                emote_get_obj_by_name(emote_handle_, "status_icon") == nullptr;
            emote_unlock(emote_handle_);
            if (clean_layout) {
                if (interaction_status_ == Lang::Strings::LISTENING || interaction_status_.find("聆听") != std::string::npos) {
                    animation = "listening";
                } else if (interaction_status_ == Lang::Strings::SPEAKING || interaction_status_.find("说话") != std::string::npos) {
                    animation = "speaking";
                } else if (interaction_status_ == Lang::Strings::STANDBY || interaction_status_ == "空闲" || interaction_status_.find("待") != std::string::npos) {
                    animation = "idle";
                }
            }
        }
        if (emote_set_anim_emoji(emote_handle_, animation) == ESP_OK) {
            explicit_emotion_ =
                std::strcmp(emotion, "neutral") != 0 && std::strcmp(emotion, "idle") != 0 &&
                std::strcmp(emotion, "listening") != 0 && std::strcmp(emotion, "speaking") != 0;
        }
        RefreshBatteryOverlay();
        RefreshInteractionOverlay();
    }
}

void EmoteDisplay::SetEventMessage(const char* event, const char* message) {
    // Callers hold overlay_mutex_, which serializes this with asset reloads.
    if (!emote_handle_ || !assets_loaded_ || !event) {
        return;
    }
    // BAT only updates the component's numeric cache. Unlike IDLE it does not
    // request any icons, and keeping it synchronized supports legacy layouts.
    if (std::strcmp(event, EMOTE_MGR_EVT_BAT) == 0) {
        emote_set_event_msg(emote_handle_, event, message);
        return;
    }
    if (emote_lock(emote_handle_) != ESP_OK) {
        return;
    }
    const bool legacy_widgets = emote_get_obj_by_name(emote_handle_, "status_icon") != nullptr &&
                                (std::strcmp(event, EMOTE_MGR_EVT_LISTEN) != 0 ||
                                 emote_get_obj_by_name(emote_handle_, "listen_anim") != nullptr);
    if (legacy_widgets) {
        emote_unlock(emote_handle_);
        emote_set_event_msg(emote_handle_, event, message);
        return;
    }
    // expression1.0.2 fetches icon resources BEFORE checking widget presence.
    // The clean layout intentionally omits these widgets/resources, so update
    // optional text directly instead of issuing an icon-bearing event.
    if (auto label = emote_get_obj_by_name(emote_handle_, "toast_label")) {
        gfx_label_set_text(label, message ? message : "");
        gfx_obj_set_visible(label, message && message[0] != '\0');
    }
    emote_unlock(emote_handle_);

    // Text/notifications must not replace an explicit emotion from touch or AI.
    // Emotion metadata may arrive before the audio START state change. Keep
    // that expression while the independent label truthfully reports speaking.
    if (!message && !explicit_emotion_) {
        if (std::strcmp(event, EMOTE_MGR_EVT_LISTEN) == 0) {
            emote_set_anim_emoji(emote_handle_, "listening");
        } else if (std::strcmp(event, EMOTE_MGR_EVT_IDLE) == 0) {
            emote_set_anim_emoji(emote_handle_, "idle");
        } else if (std::strcmp(event, EMOTE_MGR_EVT_SPEAK) == 0) {
            emote_set_anim_emoji(emote_handle_, "speaking");
        }
    }
}

void EmoteDisplay::RefreshBatteryOverlay() {
    if (emote_handle_ == nullptr || !assets_loaded_) {
        return;
    }

    if (emote_lock(emote_handle_) != ESP_OK) {
        return;
    }
    gfx_obj_t* label = emote_get_obj_by_name(emote_handle_, "battery_label");
    if (label == nullptr) {
        emote_unlock(emote_handle_);
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
    gfx_label_set_color(label, GFX_COLOR_HEX(0x22C55E));
    gfx_label_set_opa(label, 240);
    gfx_obj_set_visible(label, true);
    emote_unlock(emote_handle_);
}

void EmoteDisplay::SetInteractionMode(bool automatic) {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    automatic_mode_ = automatic;
    RefreshInteractionOverlay();
}

bool EmoteDisplay::CreateInteractionLabels() {
    // expression1.0.2's JSON loader only creates predefined widget names.
    // Custom labels must use the public by-type API so they are registered
    // for lookup and destroyed automatically by emote_unload_assets.
    struct LabelLayout {
        const char* name;
        int y;
        int width;
    };
    const LabelLayout layouts[] = {{"mode_label", 4, 60}, {"state_label", 34, 150}};
    for (const auto& layout : layouts) {
        auto label = emote_create_obj_by_type(emote_handle_, "label", layout.name);
        if (!label || emote_lock(emote_handle_) != ESP_OK) {
            return false;
        }
        gfx_obj_align(label, GFX_ALIGN_TOP_LEFT, 6, layout.y);
        // The packaged 20px font has line_height=25. A 24px label fails
        // gfx's line-height check before it paints the first glyph.
        gfx_obj_set_size(label, layout.width, 28);
        gfx_label_set_text_align(label, GFX_TEXT_ALIGN_LEFT);
        gfx_label_set_long_mode(label, GFX_LABEL_LONG_CLIP);
        gfx_obj_set_visible(label, false);
        emote_unlock(emote_handle_);
    }
    return true;
}

void EmoteDisplay::RefreshInteractionOverlay() {
    if (!emote_handle_ || !assets_loaded_ || emote_lock(emote_handle_) != ESP_OK) {
        return;
    }
    auto update_label = [this](const char* name, const char* text) {
        auto label = emote_get_obj_by_name(emote_handle_, name);
        if (!label) {
            return;
        }
        // Never fall back to the basic font: it lacks the mode's Chinese glyphs.
        const bool visible = interaction_font_ && text && text[0] != '\0';
        if (interaction_font_) {
            gfx_label_set_font(label, interaction_font_);
        }
        gfx_label_set_text(label, visible ? text : "");
        // Opaque white on black remains readable on every expression frame.
        // Custom labels are appended after both animations, so dirty animation
        // areas repaint these labels last even when their text is unchanged.
        gfx_label_set_color(label, GFX_COLOR_HEX(0xFFFFFF));
        gfx_label_set_bg_color(label, GFX_COLOR_HEX(0x000000));
        gfx_label_set_opa(label, 255);
        gfx_label_set_bg_enable(label, true);
        gfx_obj_set_visible(label, visible);
    };
    update_label("mode_label", automatic_mode_ ? "自动" : "手动");
    const char* state_text = interaction_status_.c_str();
    if (interaction_status_ == Lang::Strings::STANDBY || interaction_status_ == "待命" || interaction_status_ == "待机") {
        state_text = "空闲";
    } else if (interaction_status_ == Lang::Strings::LISTENING) {
        state_text = "聆听中";
    } else if (interaction_status_ == Lang::Strings::SPEAKING) {
        state_text = "说话中";
    }
    update_label("state_label", state_text);
    emote_unlock(emote_handle_);
}

void EmoteDisplay::SetBatteryLevel(const int level, const bool charging) {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
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
        RefreshInteractionOverlay();
        return;
    }

    // Keep the expression manager's battery cache in sync for future idle
    // events. The custom layout intentionally has no battery/status icons.
    char event_msg[16];
    std::snprintf(event_msg, sizeof(event_msg), "%d,%d", battery_charging_ ? 1 : 0,
                  battery_level_);
    SetEventMessage(EMOTE_MGR_EVT_BAT, event_msg);
    RefreshBatteryOverlay();
    RefreshInteractionOverlay();
}

void EmoteDisplay::SetChatMessage(const char* const role, const char* const content) {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    ESP_LOGI(TAG, "SetChatMessage: %s, %s", role ? role : "", content ? content : "");
    if (emote_handle_ && content && strlen(content) > 0) {
        if (role && (std::strcmp(role, "system") == 0) && std::strstr(content, "xiaozhi.me")) {
            size_t len = strlen(content);
            char* new_content = new char[len + 1];
            strcpy(new_content, content);
            std::replace(new_content, new_content + len, static_cast<char>(0x0A),
                         static_cast<char>(0x20));
            SetEventMessage(EMOTE_MGR_EVT_SYS, new_content);
            delete[] new_content;
        } else {
            SetEventMessage(EMOTE_MGR_EVT_SPEAK, content);
        }
    }
    RefreshBatteryOverlay();
    RefreshInteractionOverlay();
}

void EmoteDisplay::SetStatus(const char* const status) {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    const bool status_changed = interaction_status_ != (status ? status : "");
    interaction_status_ = status ? status : "";
    if (status_changed && (interaction_status_ == Lang::Strings::LISTENING ||
                           interaction_status_ == Lang::Strings::STANDBY)) {
        // A new listening/idle turn must not inherit the preceding reply's mood.
        explicit_emotion_ = false;
    }
    ESP_LOGI(TAG, "SetStatus: %s", status ? status : "");
    if (emote_handle_ && status && strlen(status) > 0) {
        if (std::strcmp(status, Lang::Strings::LISTENING) == 0) {
            SetEventMessage(EMOTE_MGR_EVT_LISTEN, NULL);
        } else if (std::strcmp(status, Lang::Strings::STANDBY) == 0) {
            SetEventMessage(EMOTE_MGR_EVT_IDLE, NULL);
        } else if (std::strcmp(status, Lang::Strings::SPEAKING) == 0) {
            SetEventMessage(EMOTE_MGR_EVT_SPEAK, NULL);
        } else if (std::strcmp(status, Lang::Strings::ERROR) == 0) {
            SetEventMessage(EMOTE_MGR_EVT_SET, NULL);
        }
    }
    RefreshBatteryOverlay();
    RefreshInteractionOverlay();
}

void EmoteDisplay::ShowNotification(const char* notification, int duration_ms) {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    ESP_LOGI(TAG, "ShowNotification: %s", notification ? notification : "");
    if (emote_handle_ && notification && strlen(notification) > 0) {
        SetEventMessage(EMOTE_MGR_EVT_SYS, notification);
    }
    RefreshBatteryOverlay();
    RefreshInteractionOverlay();
}

void EmoteDisplay::UpdateStatusBar(bool update_all) {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
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
        RefreshInteractionOverlay();
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
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
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
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    if (emote_handle_ != nullptr) {
        // Labels and their font adapters must disappear before either the
        // shared font descriptor or its mmap-backed glyph data are released.
        if (assets_loaded_ && emote_unload_assets(emote_handle_) != ESP_OK) {
            ESP_LOGE(TAG, "Could not unload expression assets");
            return;
        }
        assets_loaded_ = false;
        if (interaction_font_) {
            gfx_font_lv_delete(interaction_font_);
            interaction_font_ = nullptr;
        }
        emote_unmount_assets(emote_handle_);
    }
}

bool EmoteDisplay::GetAssetData(const std::string& name, const uint8_t*& data, size_t& size) {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    if (emote_handle_ == nullptr) {
        return false;
    }
    return emote_get_asset_data_by_name(emote_handle_, name.c_str(), &data, &size) == ESP_OK;
}

void EmoteDisplay::LoadAssets() {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    if (!emote_handle_) {
        return;
    }
    if (assets_loaded_ && emote_unload_assets(emote_handle_) != ESP_OK) {
        ESP_LOGE(TAG, "Could not unload expression assets for reload");
        return;
    }
    assets_loaded_ = false;
    explicit_emotion_ = false;
    if (interaction_font_) {
        gfx_font_lv_delete(interaction_font_);
        interaction_font_ = nullptr;
    }
    if (emote_load_assets(emote_handle_) != ESP_OK) {
        // The loader may have allocated tables/objects before failing. Clean
        // them now, while keeping rendering/event entry points disabled.
        emote_unload_assets(emote_handle_);
        ESP_LOGE(TAG, "Could not load expression assets");
        return;
    }
    if (!CreateInteractionLabels()) {
        emote_unload_assets(emote_handle_);
        ESP_LOGE(TAG, "Could not create interaction labels");
        return;
    }
    assets_loaded_ = true;
    const uint8_t* data = nullptr;
    size_t size = 0;
    if (emote_get_asset_data_by_name(emote_handle_, "font_puhui_common_20_4.bin", &data, &size) ==
            ESP_OK &&
        data && size > 0) {
        // One descriptor shared by both labels, no copy of the font binary.
        interaction_font_ = gfx_font_lv_load_from_binary(const_cast<uint8_t*>(data));
    }
    if (!interaction_font_) {
        ESP_LOGW(TAG, "Interaction overlay font unavailable");
    }
    // A reload must not invent a battery reading. Mode and status are cached
    // independently of expression assets and survive reloads.
    battery_level_ = -1;
    battery_charging_ = false;
    battery_valid_ = false;
    battery_override_ = false;
    RefreshBatteryOverlay();
    RefreshInteractionOverlay();
}

void EmoteDisplay::SetTheme(Theme* const theme) { ESP_LOGI(TAG, "SetTheme: %p", theme); }

bool EmoteDisplay::Lock(const int timeout_ms) {
    (void)timeout_ms;
    return true;
}

void EmoteDisplay::Unlock() {}

bool EmoteDisplay::StopAnimDialog() {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    ESP_LOGI(TAG, "StopAnimDialog");
    if (emote_handle_) {
        return emote_stop_anim_dialog(emote_handle_);
    }
    return false;
}

bool EmoteDisplay::InsertAnimDialog(const char* emoji_name, uint32_t duration_ms) {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    ESP_LOGI(TAG, "InsertAnimDialog: %s, %" PRIu32, emoji_name ? emoji_name : "", duration_ms);
    if (emote_handle_ && assets_loaded_ && emoji_name) {
        return emote_insert_anim_dialog(emote_handle_, emoji_name, duration_ms);
    }
    return false;
}

void EmoteDisplay::RefreshAll() {
    std::lock_guard<std::recursive_mutex> guard(overlay_mutex_);
    if (emote_handle_) {
        emote_notify_all_refresh(emote_handle_);
        return;
    }
}

}  // namespace emote
