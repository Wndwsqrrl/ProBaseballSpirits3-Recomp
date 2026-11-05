// prospi3 - ReXGlue Recompiled Project
//
// Customize your app by overriding virtual hooks from rex::ReXApp.

#pragma once

#include <rex/rex_app.h>
#include "english_patch.h"
#include "text_localization.h"
#include "keyboard_taps.h"
#include "performance.h"
void InstallPortDiagnostics();
void ConfigurePreferredGpu();

class Prospi3App : public rex::ReXApp {
 public:
  using rex::ReXApp::ReXApp;

  static std::unique_ptr<rex::ui::WindowedApp> Create(
      rex::ui::WindowedAppContext& ctx) {
    return std::unique_ptr<Prospi3App>(new Prospi3App(ctx, "prospi3",
        PPCImageConfig));
  }

  void OnPreSetup(rex::RuntimeConfig& config) override {
    ConfigurePreferredGpu();
    if (config.gpu_plugin.empty()) config.gpu_plugin = "xenos";
  }

  void OnPostLoadXexImage() override {
    InitializePerformance(*runtime());
    InitializeTextLocalization(*runtime());
    ApplyEnglishPatch(*runtime());
  }
  void OnPostInitLogging() override { InstallPortDiagnostics(); }
  void OnPostSetup() override { InstallKeyboardTapSupport(window()); }
  void OnShutdown() override { WritePerformanceReport(); RemoveKeyboardTapSupport(window()); }

  // Override virtual hooks for customization:
  // void OnPostInitLogging() override {}
  // void OnPreSetup(rex::RuntimeConfig& config) override {}
  // void OnLoadXexImage(std::string& xex_image) override {}
  // void OnPostLoadXexImage() override {}
  // void OnPostSetup() override {}
  // void OnCreateDialogs(rex::ui::ImGuiDrawer* drawer) override {}
  // std::unique_ptr<rex::ui::ImGuiDialog> CreateAchievementsOverlay() override;
  // std::unique_ptr<rex::ui::AchievementNotificationDialog>
  // CreateAchievementNotificationDialog() override;
  // void OnShutdown() override {}
  // void OnConfigurePaths(rex::PathConfig& paths) override {}
};
