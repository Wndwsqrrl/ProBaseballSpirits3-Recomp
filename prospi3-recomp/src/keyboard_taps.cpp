// Preserve brief keyboard taps until the guest has time to poll controller state.
// Input still comes from normal window key events; physical pads are untouched.
#include "keyboard_taps.h"
#include <array>
#include <atomic>
#include <chrono>
#include <cstring>
#include <rex/logging.h>
#include <rex/ppc/context.h>
#include <rex/ppc/func.h>
#include <rex/ui/window.h>
#include <rex/ui/window_listener.h>

namespace {
using Clock=std::chrono::steady_clock;
uint64_t Now() { return std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now().time_since_epoch()).count(); }
std::array<std::atomic<uint64_t>,16> deadlines{};
std::array<std::atomic<bool>,16> held{};
std::atomic<uint32_t> packet{0};
uint16_t Button(uint16_t key) {
  switch(key) {
    case 0x0D: case 'X': return 0x0010; // Start
    case 0x20: case 0xBA: return 0x1000; // A
    case 0x08: case 0xDE: return 0x2000; // B
    case 'L': return 0x4000;
    case 'P': return 0x8000;
    case 'W': case 0x26: return 0x0001;
    case 'S': case 0x28: return 0x0002;
    case 'A': case 0x25: return 0x0004;
    case 'D': case 0x27: return 0x0008;
    case '1': return 0x0100;
    case '3': return 0x0200;
    case 'Z': case 0x09: return 0x0020;
    default:return 0;
  }
}
class TapListener : public rex::ui::WindowInputListener, public rex::ui::WindowListener {
 public:
  void OnKeyDown(rex::ui::KeyEvent& event) override {
    if(event.is_alt_pressed() || event.is_ctrl_pressed()) return;
    const auto button=Button(static_cast<uint16_t>(event.virtual_key()));
    if(!button)return;
    for(unsigned i=0;i<16;++i)if(button&(1u<<i)) {
      deadlines[i].store(Now()+140,std::memory_order_relaxed);
      held[i].store(true,std::memory_order_relaxed);
    }
    ++packet;
  }
  void OnKeyUp(rex::ui::KeyEvent& event) override {
    const auto button=Button(static_cast<uint16_t>(event.virtual_key()));
    for(unsigned i=0;i<16;++i)if(button&(1u<<i))held[i].store(false,std::memory_order_relaxed);
  }
  void OnLostFocus(rex::ui::UISetupEvent&) override {
    for(unsigned i=0;i<16;++i) { held[i].store(false); deadlines[i].store(0); }
  }
} listener;
}

void InstallKeyboardTapSupport(rex::ui::Window* window) {
  if(window) { window->AddInputListener(&listener,0); window->AddListener(&listener); }
}
void RemoveKeyboardTapSupport(rex::ui::Window* window) {
  if(window) { window->RemoveInputListener(&listener); window->RemoveListener(&listener); }
}

REX_EXTERN(__imp__sub_8262F888);
REX_EXTERN(sub_8262F888) {
  const uint32_t user=ctx.r3.u32, output=ctx.r4.u32;
  __imp__sub_8262F888(ctx,base);
  if(user || !output)return;
  uint16_t buttons=0;
  const auto now=Now();
  for(unsigned i=0;i<16;++i)if(held[i].load(std::memory_order_relaxed) || now<deadlines[i].load(std::memory_order_relaxed))buttons|=uint16_t(1u<<i);
  if(!buttons)return;
  auto* state=base+output;
  if(ctx.r3.u32)std::memset(state,0,16);
  const uint16_t old=uint16_t((uint16_t(state[4])<<8)|state[5]);
  const uint16_t merged=old|buttons;
  state[4]=uint8_t(merged>>8);state[5]=uint8_t(merged);
  const uint32_t number=packet.load(std::memory_order_relaxed);
  state[0]=uint8_t(number>>24);state[1]=uint8_t(number>>16);state[2]=uint8_t(number>>8);state[3]=uint8_t(number);
  ctx.r3.u64=0;
}
