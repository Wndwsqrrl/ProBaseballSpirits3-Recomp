#pragma once

#include <optional>
#include <string>
#include <string_view>

namespace localization {

inline std::optional<std::string> PrepareOffseasonMessage(std::string_view message) {
  // The native formatter copies up to three 32-character rows. It skips the
  // highlight controls and passes its input through sprintf before splitting.
  constexpr unsigned kRows = 3;
  constexpr unsigned kColumns = 32;
  unsigned rows = 1;
  unsigned columns = 0;
  std::string format;
  for (unsigned char character : message) {
    if (character == '\n') {
      if (++rows > kRows || columns == 0) return std::nullopt;
      columns = 0;
    } else if (character == '\v') {
      if (columns == kColumns) return std::nullopt;
    } else {
      if (character < ' ' || character > '~' || ++columns > kColumns) return std::nullopt;
      if (character == '%') format += '%';
    }
    format += static_cast<char>(character);
  }
  if (columns == 0) return std::nullopt;
  return format;
}

inline constexpr char16_t kTestPcIpDescription[] = u"Enter the IP address of the test PC.";

}  // namespace localization
