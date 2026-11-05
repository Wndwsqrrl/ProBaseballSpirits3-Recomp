#pragma once
#include <cstdint>
namespace rex { class Runtime; }
enum class TextPhase : unsigned { Markup, Measure, Raster };
extern bool gPerformanceEnabled;
void InitializePerformance(rex::Runtime& runtime);
void WritePerformanceReport();
class TextProfileScope {
 public:
  explicit TextProfileScope(TextPhase phase):phase_(phase){Resume();}
  ~TextProfileScope(){if(gPerformanceEnabled)Finish();}
  void Suspend(){if(start_)SuspendActive();}
  void Resume(){if(gPerformanceEnabled)ResumeActive();}
 private:
  TextPhase phase_;
  uint64_t start_=0;
  void SuspendActive();
  void ResumeActive();
  void Finish();
};
