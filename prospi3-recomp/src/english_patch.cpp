#include "english_patch.h"
#include "generated/translation/english_strings.h"
#include "generated/translation/hanshin_names.h"
#include "generated/translation/all_roster_names.h"
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <string_view>
#include <rex/logging.h>
#include <rex/runtime.h>
#include <rex/system/xmemory.h>

void ApplyEnglishPatch(rex::Runtime& runtime) {
  const char* enabled = std::getenv("PROSPI3_ENGLISH");
  if (!enabled || std::string_view(enabled) != "1") return;
  auto* memory = runtime.memory();
  for(const auto& entry:kAllRosterNames) {
    const auto* bytes=memory->TranslateVirtual(entry.address);uint64_t hash=0xCBF29CE484222325ULL;
    for(uint32_t i=0;i<entry.size;++i)hash=(hash^bytes[i])*0x100000001B3ULL;
    if(hash!=entry.hash || entry.english.size()>=entry.size)
      throw std::runtime_error("Roster patch rejected: original field differs");
  }
  for (const auto& entry : kHanshinNames) {
    const auto* bytes=memory->TranslateVirtual(entry.address);
    uint64_t hash=0xCBF29CE484222325ULL;
    for(uint32_t i=0;i<entry.size;++i)hash=(hash^bytes[i])*0x100000001B3ULL;
    if(hash!=entry.hash || entry.english.size()>=entry.size)
      throw std::runtime_error("Hanshin roster patch rejected: original field differs");
  }
  // Validate every string before writing anything; this patch targets one image.
  for (const auto& entry : kEnglishStrings) {
    const auto* bytes = memory->TranslateVirtual(entry.address);
    if (std::memcmp(bytes, entry.original.data(), entry.original.size()) != 0 ||
        bytes[entry.original.size()] != 0) {
      throw std::runtime_error("English patch rejected: original string bytes differ");
    }
  }
  for (const auto& entry : kEnglishStrings) {
    auto* heap = memory->LookupHeap(entry.address);
    uint32_t original_protection = 0;
    const auto length = static_cast<uint32_t>(entry.original.size() + 1);
    if (!heap || !heap->Protect(entry.address, length,
          rex::memory::kMemoryProtectRead | rex::memory::kMemoryProtectWrite,
          &original_protection)) {
      throw std::runtime_error("Cannot make English string writable");
    }
    auto* bytes = memory->TranslateVirtual(entry.address);
    std::memset(bytes, 0, length);
    std::memcpy(bytes, entry.english.data(), entry.english.size());
    if (!heap->Protect(entry.address, length, original_protection))
      throw std::runtime_error("Cannot restore string memory protection");
  }
  REXLOG_INFO("Experimental English patch: {} strings applied", std::size(kEnglishStrings));
  for(const auto& entry:kHanshinNames) {
    auto* bytes=memory->TranslateVirtual(entry.address);
    std::memset(bytes,0,entry.size);
    std::memcpy(bytes,entry.english.data(),entry.english.size());
  }
  REXLOG_INFO("Hanshin roster: {} bounded name fields applied",std::size(kHanshinNames));
  for(const auto& entry:kAllRosterNames) {
    auto* bytes=memory->TranslateVirtual(entry.address);
    std::memset(bytes,0,entry.size);std::memcpy(bytes,entry.english.data(),entry.english.size());
  }
  REXLOG_INFO("Other roster records: {} bounded name fields applied",std::size(kAllRosterNames));
}
