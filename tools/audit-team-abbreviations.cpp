// Offline guard and byte-bound checks against the supported loaded image.
#include "../prospi3-recomp/src/team_abbreviations.h"
#include <algorithm>
#include <array>
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

#ifdef NDEBUG
#error Compile this audit with assertions enabled.
#endif

int main(int argc, char** argv) {
  if (argc != 2) return 2;
  using namespace localization;
  constexpr uint32_t image_base = 0x82000000, pool_base = 0x10000000;
  std::ifstream input(argv[1], std::ios::binary);
  std::vector<uint8_t> image((std::istreambuf_iterator<char>(input)), {});
  if (image.size() < kTeamAbbreviationTable - image_base + 124) return 3;
  const auto original = image;
  std::array<uint8_t, kTeamAbbreviationPoolSize + 1> pool;
  pool.fill(0xA5);
  size_t writes = 0;
  auto read = [&](uint32_t address) {
    const auto i = address - image_base;
    assert(address >= image_base && uint64_t(i) + 4 <= image.size());
    return uint32_t(image[i]) << 24 | uint32_t(image[i + 1]) << 16 |
           uint32_t(image[i + 2]) << 8 | image[i + 3];
  };
  auto word = [&](uint32_t address, uint32_t value) {
    assert(address >= kTeamAbbreviationTable &&
           address < kTeamAbbreviationTable + 124 && !(address & 3));
    for (size_t j = 0; j < 4; ++j)
      image[address - image_base + j] = uint8_t(value >> ((3 - j) * 8));
    ++writes;
  };
  auto byte = [&](uint32_t address, uint8_t value) {
    assert(address >= pool_base && address < pool_base + kTeamAbbreviationPoolSize);
    pool[address - pool_base] = value;
    ++writes;
  };
  if (!IsOriginalTeamAbbreviationTable(read)) return 4;
  for (uint32_t invalid : {0u, 0xFFFFFFF0u, kTeamAbbreviationTable,
                           kTeamAbbreviationTable - 1}) {
    assert(!InstallTeamAbbreviations(invalid, read, word, byte));
    assert(!writes);
  }
  auto mismatch = [&](uint32_t address) {
    return read(address) ^ (address == kTeamAbbreviationTable + 120 ? 4u : 0u);
  };
  assert(!InstallTeamAbbreviations(pool_base, mismatch, word, byte));
  assert(!writes);
  assert(InstallTeamAbbreviations(pool_base, read, word, byte));
  assert(writes == 124 && pool.back() == 0xA5);
  auto label = [&](size_t id) {
    const auto offset = read(kTeamAbbreviationTable + uint32_t(id * 4)) - pool_base;
    assert(offset == id * 3 && pool[offset + 2] == 0);
    return std::string(reinterpret_cast<const char*>(pool.data() + offset));
  };
  for (size_t i = 0; i < 31; ++i)
    assert(label(i) == kTeamAbbreviations[i].english && label(i).size() <= 2);
  assert(label(1) == "D" && label(15) == "D" && label(28) == "CN");
  assert(label(22) == "I" && label(26) == "EL");
  assert(label(4) == "YB" && label(18) == "SR" && label(23) == "SU");
  assert(label(29) == "KR" && label(30) == "CT");
  for (size_t i = 0; i < image.size(); ++i) {
    if (i >= kTeamAbbreviationTable - image_base &&
        i < kTeamAbbreviationTable - image_base + 124) continue;
    assert(image[i] == original[i]);
  }
  writes = 0;
  assert(!InstallTeamAbbreviations(pool_base, read, word, byte));
  assert(!writes);
  std::cout << "31 compact team labels, shared-source contexts, pool bounds and "
               "original-image preservation passed.\n";
}
