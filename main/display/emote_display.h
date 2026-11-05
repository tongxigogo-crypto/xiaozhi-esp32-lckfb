#pragma once

#include <esp_lcd_panel_io.h>
#include <esp_lcd_panel_ops.h>
#include <lvgl.h>
#include <memory>
#include <mutex>
#include <string>
#include "display.h"
#include "expression_emote.h"

namespace emote {

class EmoteDisplay : public Display {
public:
    using Display::SetPreviewImage;

    EmoteDisplay(esp_lcd_panel_handle_t panel, esp_lcd_panel_io_handle_t panel_io, int width,
                 int height);
    virtual ~EmoteDisplay();

    virtual void SetEmotion(const char* emotion) override;
    // Update the optional battery percentage overlay. A negative level hides it.
    void SetBatteryLevel(int level, bool charging);
    virtual void SetStatus(const char* status) override;
    virtual void SetInteractionMode(bool automatic) override;
    virtual void SetChatMessage(const char* role, const char* content) override;
    virtual void SetTheme(Theme* theme) override;
    virtual void ShowNotification(const char* notification, int duration_ms = 3000) override;
    virtual void UpdateStatusBar(bool update_all = false) override;
    virtual void SetPowerSaveMode(bool on) override;
    virtual void SetPreviewImage(const void* image);

    bool StopAnimDialog();
    virtual bool InsertAnimDialog(const char* emoji_name, uint32_t duration_ms) override;
    virtual bool MountAssets(const char* partition_label) override;
    virtual void UnmountAssets() override;
    virtual bool GetAssetData(const std::string& name, const uint8_t*& data, size_t& size) override;
    virtual void LoadAssets() override;

    void RefreshAll();

    // Get emote handle for internal use
    emote_handle_t GetEmoteHandle() const { return emote_handle_; }

private:
    // Helpers require overlay_mutex_; each takes the graphics lock internally.
    // Adapt legacy status events to layouts without status icons.
    void SetEventMessage(const char* event, const char* message);
    void RefreshBatteryOverlay();
    void RefreshInteractionOverlay();
    bool CreateInteractionLabels();

    virtual bool Lock(int timeout_ms = 0) override;
    virtual void Unlock() override;

    emote_handle_t emote_handle_ = nullptr;
    // Public setters call other public setters (e.g. battery polling).
    // Serialize them with asset reloads; always take this before emote_lock.
    std::recursive_mutex overlay_mutex_;
    lv_font_t* interaction_font_ = nullptr;
    bool assets_loaded_ = false;
    bool automatic_mode_ = true;
    std::string interaction_status_;
    int battery_level_ = -1;
    bool battery_charging_ = false;
    bool battery_valid_ = false;
    bool battery_override_ = false;
};

}  // namespace emote
