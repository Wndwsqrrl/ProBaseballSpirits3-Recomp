#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace localization {
constexpr uint32_t kTeamAbbreviationTable = 0x8273E668;
struct TeamAbbreviation {
  uint32_t original;
  std::string_view english;
};
// Team IDs follow the native parallel full-name and compact-name tables.
// Keep every replacement within the two CP932 bytes used by the source glyph.
constexpr std::array<TeamAbbreviation, 31> kTeamAbbreviations{{
    {0x820A6780, "G"}, {0x820830E0, "D"}, {0x820A677C, "C"},
    {0x820A6778, "YS"}, {0x820A6774, "YB"}, {0x820A6770, "T"},
    {0x820A676C, "E"}, {0x82088970, "F"}, {0x820A6768, "L"},
    {0x8208A0D8, "Bs"}, {0x82089C8C, "M"}, {0x8208A0A0, "H"},
    {0x820A6764, "CL"}, {0x820A6760, "PL"},
    {0x820A6780, "G"}, {0x820830E0, "D"}, {0x820A677C, "C"},
    {0x820A6778, "YS"}, {0x820A675C, "SR"}, {0x820A6770, "T"},
    {0x820A676C, "E"}, {0x82088970, "F"}, {0x8208BCD8, "I"},
    {0x820A6758, "SU"}, {0x82089C8C, "M"}, {0x8208A0A0, "H"},
    {0x8208BCD8, "EL"}, {0x820A6754, "WL"},
    {0x820830E0, "CN"}, {0x820A6750, "KR"}, {0x820A674C, "CT"},
}};
constexpr uint32_t kTeamAbbreviationPoolSize = kTeamAbbreviations.size() * 3;
static_assert([] {
  for (const auto& row : kTeamAbbreviations)
    if (row.english.empty() || row.english.size() > 2) return false;
  return true;
}());

template <typename ReadWord>
bool IsOriginalTeamAbbreviationTable(ReadWord read_word) {
  for (std::size_t i = 0; i < kTeamAbbreviations.size(); ++i)
    if (read_word(kTeamAbbreviationTable + uint32_t(i * 4)) !=
        kTeamAbbreviations[i].original) return false;
  return true;
}

template <typename ReadWord, typename WriteWord, typename WriteByte>
bool InstallTeamAbbreviations(uint32_t pool, ReadWord read_word,
                              WriteWord write_word, WriteByte write_byte) {
  if (!pool || pool > UINT32_MAX - kTeamAbbreviationPoolSize ||
      !IsOriginalTeamAbbreviationTable(read_word)) return false;
  constexpr auto table_end = kTeamAbbreviationTable + kTeamAbbreviations.size() * 4;
  if (pool < table_end && pool + kTeamAbbreviationPoolSize > kTeamAbbreviationTable)
    return false;
  // Only this column changes. Shared source strings such as 中 (center field,
  // Chunichi, China) and イ (Invoice, Eastern) keep their original bytes.
  for (std::size_t i = 0; i < kTeamAbbreviations.size(); ++i) {
    const auto address = pool + uint32_t(i * 3);
    const auto text = kTeamAbbreviations[i].english;
    for (std::size_t j = 0; j < 3; ++j)
      write_byte(address + uint32_t(j), j < text.size() ? uint8_t(text[j]) : 0);
  }
  for (std::size_t i = 0; i < kTeamAbbreviations.size(); ++i)
    write_word(kTeamAbbreviationTable + uint32_t(i * 4), pool + uint32_t(i * 3));
  return true;
}
}  // namespace localization
