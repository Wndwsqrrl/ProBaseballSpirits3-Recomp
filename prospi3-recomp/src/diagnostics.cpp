#include <rex/logging.h>
#include <spdlog/sinks/base_sink.h>
#include <mutex>
#include <cstdlib>
#include <string_view>
void ReportActiveTextTrap();
#ifdef _WIN32
#include <Windows.h>
void ReportCleanupStack() {
  void* frames[32]{};
  const auto count=CaptureStackBackTrace(0,32,frames,nullptr);
  const auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
  for(unsigned i=0;i<count;++i) {
    const auto address=reinterpret_cast<uintptr_t>(frames[i]);
    REXLOG_CRITICAL("Cleanup stack frame {}: address={:016X}, exe-offset={:X}",i,address,address-base);
  }
}
namespace {
class GuestTrapTrace : public spdlog::sinks::base_sink<std::mutex> {
  bool recorded=false;
  void sink_it_(const spdlog::details::log_msg& message) override {
    if(recorded || std::string_view(message.payload.data(),message.payload.size()).find("tw/td trap hit")==std::string_view::npos)return;
    recorded=true;
    ReportActiveTextTrap();
    void* frames[32]{};
    const auto count=CaptureStackBackTrace(0,32,frames,nullptr);
    const auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    REXLOG_CRITICAL("First guest trap: capturing native stack; repeated trap warnings suppressed.");
    for(unsigned i=0;i<count;++i) {
      const auto address=reinterpret_cast<uintptr_t>(frames[i]);
      REXLOG_CRITICAL("Guest-trap stack frame {}: address={:016X}, exe-offset={:X}",i,address,address-base);
    }
    if(auto* cpu=rex::GetLoggerRaw(rex::log::cpu()))cpu->set_level(spdlog::level::err);
    if(auto* core=rex::GetLoggerRaw(rex::log::core()))core->flush();
  }
  void flush_() override {}
};
LONG CALLBACK ReportNativeFault(EXCEPTION_POINTERS* fault) {
  const DWORD code = fault->ExceptionRecord->ExceptionCode;
  if (code == EXCEPTION_FLT_INEXACT_RESULT || code == EXCEPTION_FLT_INVALID_OPERATION ||
      code == EXCEPTION_ACCESS_VIOLATION) {
    const auto base = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    REXLOG_CRITICAL("Native fault code={:08X} RIP={:016X} exe-offset={:X} MXCSR={:08X} x87-control={:04X}",
        code, fault->ContextRecord->Rip, fault->ContextRecord->Rip - base,
        fault->ContextRecord->MxCsr, fault->ContextRecord->FltSave.ControlWord);
    if (auto* logger = rex::GetLoggerRaw(rex::log::core())) logger->flush();
  }
  return EXCEPTION_CONTINUE_SEARCH;
}
}
#endif
#ifndef _WIN32
void ReportCleanupStack() {}
#endif
void InstallPortDiagnostics() {
  const auto* verbose_audio=std::getenv("PROSPI3_VERBOSE_AUDIO");
  if(!verbose_audio || std::string_view(verbose_audio)!="1") {
    if(auto* apu=rex::GetLoggerRaw(rex::log::apu()))apu->set_level(spdlog::level::err);
    REXLOG_INFO("Audio warning flood suppressed for gameplay; decoding errors remain enabled. Set PROSPI3_VERBOSE_AUDIO=1 for decoder diagnostics.");
  }
#ifdef _WIN32
  AddVectoredExceptionHandler(1, ReportNativeFault);
  if(auto* cpu=rex::GetLoggerRaw(rex::log::cpu()))cpu->sinks().push_back(std::make_shared<GuestTrapTrace>());
#endif
}
