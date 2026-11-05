#pragma once
#include <algorithm>
#include <cstdint>
#include <string_view>

namespace localization {
// Fit the widest line, including lines after the heading of a tooltip.
template<class Advance>
uint32_t MaxLineWidth(std::string_view text, Advance advance) {
  uint32_t line=0, widest=0;
  for(unsigned char c:text) {
    if(c=='\n' || c=='\r') {
      widest=std::max(widest,line);
      line=0;
    } else {
      line+=advance(c);
    }
  }
  return std::max(widest,line);
}
}
