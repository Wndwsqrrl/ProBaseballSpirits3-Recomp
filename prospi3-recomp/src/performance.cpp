#include "performance.h"
#include <rex/runtime.h>
#include <rex/logging.h>
#include <rex/ppc/func.h>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <string_view>
#include <vector>

bool gPerformanceEnabled=false;
namespace {
using Clock=std::chrono::steady_clock;
uint64_t Now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();}
std::array<std::atomic<uint64_t>,3> text_ns{},text_calls{};
std::filesystem::path output;
std::mutex frame_mutex;
struct Frame { uint64_t elapsed, interval, text; };
std::vector<Frame> frames;
std::ofstream live_profile;
uint64_t first_frame=0,last_frame=0,last_text=0;
void RecordFrame() {
  if(!gPerformanceEnabled)return;
  std::lock_guard guard(frame_mutex);
  const auto now=Now();
  uint64_t text=0;
  for(auto& counter:text_ns)text+=counter.load(std::memory_order_relaxed);
  if(!first_frame)first_frame=now;
  if(last_frame && frames.size()<360000) {
    const Frame frame{now-first_frame,now-last_frame,text-last_text};
    frames.push_back(frame);
    if(live_profile) {
      live_profile<<double(frame.elapsed)/1e6<<','<<double(frame.interval)/1e6<<','<<double(frame.text)/1e6<<'\n';
      if(frames.size()%120==0)live_profile.flush();
    }
  }
  last_frame=now;last_text=text;
}
}
void InitializePerformance(rex::Runtime& runtime) {
  const auto* enabled=std::getenv("PROSPI3_PROFILE");
  gPerformanceEnabled=enabled && std::string_view(enabled)=="1";
  if(!gPerformanceEnabled)return;
  const auto* english=std::getenv("PROSPI3_ENGLISH");
  const bool localized=english && std::string_view(english)=="1";
  output=runtime.user_data_root()/(localized?"performance-english.csv":"performance-japanese.csv");
  if(const auto* label=std::getenv("PROSPI3_PROFILE_LABEL")) {
    const std::string_view value(label);
    if(!value.empty() && value.size()<64 && value.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")==std::string_view::npos)
      output=runtime.user_data_root()/(std::string("performance-")+std::string(value)+".csv");
  }
  frames.reserve(36000);
  std::filesystem::create_directories(output.parent_path());
  live_profile.open(output);
  if(!live_profile) {gPerformanceEnabled=false;REXLOG_WARN("Cannot open frame profile: {}",output.string());return;}
  live_profile<<"elapsed_ms,frame_interval_ms,text_hook_cpu_ms\n";
  live_profile.flush();
  REXLOG_INFO("Performance profiling enabled: {}",output.string());
}
void TextProfileScope::Finish(){Suspend();text_calls[unsigned(phase_)].fetch_add(1,std::memory_order_relaxed);}
void TextProfileScope::SuspendActive(){
  text_ns[unsigned(phase_)].fetch_add(Now()-start_,std::memory_order_relaxed);
  start_=0;
}
void TextProfileScope::ResumeActive(){start_=Now();}
void WritePerformanceReport() {
  if(!gPerformanceEnabled)return;
  std::lock_guard guard(frame_mutex);
  live_profile.flush();
  constexpr const char* names[]={"markup","measure","raster"};
  for(unsigned i=0;i<3;++i)
    REXLOG_INFO("Text hook profile {}: calls={}, own CPU ms={} (guest rendering excluded)",names[i],text_calls[i].load(),double(text_ns[i].load())/1e6);
  REXLOG_INFO("Performance report: {} submitted-frame intervals; GPU completion is not measured",frames.size());
}
REX_EXTERN(__imp__sub_8263DBB8);
// This guest D3D function contains the executable's sole VdSwap call. Measure
// submission cadence without altering its arguments, return value or pacing.
REX_EXTERN(sub_8263DBB8) {
  RecordFrame();
  __imp__sub_8263DBB8(ctx,base);
}
