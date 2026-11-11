#include "text_localization.h"
#include "announced_names.h"
#include "latin_font.h"
#include "performance.h"
#include "format_translation.h"
#include "text_layout.h"
#include "report_translation.h"
#include "generated/translation/full_text.h"
#include <cstdlib>
#include <bit>
#include <algorithm>
#include <cstddef>
#include <cstring>
#include <fstream>
#include <mutex>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <rex/logging.h>
#include <rex/ppc/context.h>
#include <rex/ppc/func.h>
#include <rex/runtime.h>
#include <rex/system/xam/content_manager.h>
#include <rex/system/xmemory.h>

REX_EXTERN(__imp__sub_8260E870);
REX_EXTERN(__imp__sub_8260EDE0);
REX_EXTERN(__imp__sub_8260D8B0);
REX_EXTERN(__imp__sub_8260F470);
REX_EXTERN(__imp__sub_82413358);
REX_EXTERN(__imp__sub_825DEAC8);
REX_EXTERN(__imp__sub_825DF6A8);
REX_EXTERN(__imp__sub_82548958);
REX_EXTERN(__imp__sub_8254C0A8);
REX_EXTERN(__imp__sub_826BA910);
REX_EXTERN(__imp__sub_8262FB40);
REX_EXTERN(__imp__sub_82135D68);
REX_EXTERN(__imp__sub_823825F8);
REX_EXTERN(__imp__sub_82382B10);
REX_EXTERN(__imp__sub_823831A8);

namespace {
rex::memory::Memory* memory = nullptr;
std::unordered_map<uint64_t, uint32_t> translations;
std::unordered_map<uint64_t, uint32_t> announced_names;
std::unordered_map<uint16_t, uint32_t> announced_kana;
std::mutex announced_grid_mutex;
std::unordered_set<uint32_t> announced_grid_objects;
thread_local bool romanized_announced_grid = false;
std::mutex trace_mutex;
std::unordered_set<uint64_t> traced;
std::ofstream untranslated;
std::ofstream short_text;
std::unordered_set<uint64_t> traced_short;
std::unordered_set<uint64_t> short_labels;
bool trace_text=false;
bool latin_font_enabled=true;
std::vector<localization::FormatTranslation> format_translations;
localization::ReportTranslation report_translations;
std::unordered_map<uint32_t,localization::FormatTranslation> contextual_formats;
std::mutex dynamic_mutex;
std::unordered_map<std::string,uint32_t> dynamic_cache;
uint32_t dynamic_pool=0,dynamic_used=0;
constexpr uint32_t kDynamicPoolSize=8*1024*1024;
struct QuadCapacity {uint32_t original;bool exceeded=false;};
std::mutex quad_mutex;
std::unordered_map<uint32_t,QuadCapacity> quad_capacities;
thread_local PPCContext* active_text_context=nullptr;
thread_local uint32_t active_text_address=0;
thread_local uint32_t active_text_object=0;
thread_local std::optional<uint32_t> scoring_play_runs;

uint64_t Fingerprint(std::string_view text) {
  uint64_t value = 0xCBF29CE484222325ULL;
  for (unsigned char byte : text) value = (value ^ byte) * 0x100000001B3ULL;
  return value;
}
uint32_t Read32(uint32_t address) {
  const auto* bytes = memory->TranslateVirtual(address);
  return (uint32_t(bytes[0])<<24) | (uint32_t(bytes[1])<<16) | (uint32_t(bytes[2])<<8) | bytes[3];
}
void Write32(uint32_t address, uint32_t value) {
  auto* bytes = memory->TranslateVirtual(address);
  bytes[0]=uint8_t(value>>24); bytes[1]=uint8_t(value>>16); bytes[2]=uint8_t(value>>8); bytes[3]=uint8_t(value);
}
bool IsLatin(uint32_t address) {
  if(!address)return false;
  const auto* text=memory->TranslateVirtual(address);
  for(size_t i=0;i<8192;++i) {
    if(!text[i])return true;
    if(text[i]>=0x80)return false;
  }
  return false;
}
uint32_t LatinCache(uint32_t object) {
  if(!latin_font_enabled)return 0;
  const auto japanese=Read32(object+4),latin=Read32(object+8);
  const auto original=japanese?japanese:latin;
  return original?GetLatinFontCache(*memory,Read32(original+24)):0;
}

uint32_t TranslateFormatted(std::string_view source, bool career_speaker=false) {
  // Both successes and misses are cached. Repeated HUD draws do not rematch
  // every template, and a changing season/game clock cannot grow without bound.
  if(source.size()>1024)return 0;
  std::lock_guard guard(dynamic_mutex);
  std::string key(source);
  if(career_speaker)key+='\0';
  if(auto it=dynamic_cache.find(key);it!=dynamic_cache.end())return it->second;
  if(dynamic_cache.size()>=8192) {
    // Old misses must not prevent later modes or season statistics from being
    // translated. Positive guest pointers remain stable for retained text objects.
    for(auto it=dynamic_cache.begin();it!=dynamic_cache.end();)
      if(!it->second)it=dynamic_cache.erase(it);else ++it;
  }
  if(dynamic_cache.size()>=65536 || !dynamic_pool)return 0;
  const auto translate_name=[](std::string_view capture) {
    if(auto it=translations.find(Fingerprint(capture));it!=translations.end())
      return std::string(reinterpret_cast<const char*>(memory->TranslateVirtual(it->second)));
    return std::string(capture);
  };
  std::optional<std::string> result;
  if(career_speaker) {
    result=localization::CareerSpeaker(source,[&](std::string_view name) {
      name=localization::TrimDisplayPadding(name);
      auto translated=translate_name(name);
      if(auto normalized=localization::NormalizeFullwidthAscii(translated))return *normalized;
      return translated;
    });
  } else {
    result=localization::NormalizeFullwidthAscii(source);
    if(!result)result=report_translations.Apply(source);
    for(const auto& format:format_translations) {
      auto candidate=format.Apply(source,translate_name);
      if(!candidate)continue;
      // A short label may match several templates. Do not guess if they disagree.
      if(result && *candidate!=*result) {dynamic_cache.emplace(key,0);return 0;}
      result=std::move(candidate);
    }
  }
  uint32_t address=0;
  if(result && dynamic_used+result->size()+1<=kDynamicPoolSize) {
    address=dynamic_pool+dynamic_used;
    std::memcpy(memory->TranslateVirtual(address),result->c_str(),result->size()+1);
    dynamic_used+=uint32_t(result->size()+1);
  }
  dynamic_cache.emplace(key,address);
  return address;
}

uint32_t Translate(uint32_t address,bool whole_run=false,uint32_t caller=0) {
  if (!memory || !address) return address;
  const auto* bytes = reinterpret_cast<const char*>(memory->TranslateVirtual(address));
  size_t length = 0;
  bool japanese = false;
  while (length < 8192 && bytes[length]) {
    japanese |= static_cast<unsigned char>(bytes[length]) >= 0x80;
    ++length;
  }
  if (length == 8192) return address;
  // Every source key in the translation catalogue contains non-ASCII bytes.
  // Already-English runs need neither hashing nor a catalogue lookup.
  if(!japanese)return address;
  const std::string_view source(bytes, length);
  // Do not translate one Japanese glyph from a larger name or sentence.
  // Static one-character labels retain their address-based relocation.
  const auto fingerprint = Fingerprint(source);
  if(!whole_run && length<=2 && !(address>=0x82000400 && address<0x820AB20C)) {
    // The markup parser sends fragments of unknown names one glyph at a time.
    // Other callers send complete stat labels. Permit only the reviewed short
    // HUD labels there; keep arbitrary name/sentence fragments intact.
    const bool markup=caller>=0x82413358 && caller<0x82413BF0;
    if(trace_text) {
      std::lock_guard guard(trace_mutex);
      if(traced_short.insert(fingerprint^uint64_t(caller)).second && short_text) {
        short_text<<std::hex<<address<<'\t'<<caller<<'\t';
        constexpr char digits[]="0123456789ABCDEF";
        for(unsigned char byte:source)short_text<<digits[byte>>4]<<digits[byte&15];
        short_text<<'\n';short_text.flush();
      }
    }
    if(markup || !short_labels.contains(fingerprint))return address;
  }
  if (const auto it = translations.find(fingerprint); it != translations.end()) return it->second;
  size_t first=0,last=source.size();
  while(first<last && source[first]==' ')++first;
  while(last>first && source[last-1]==' ')--last;
  if(first || last<source.size()) {
    if(const auto it=translations.find(Fingerprint(source.substr(first,last-first)));it!=translations.end())return it->second;
  }
  std::string compact;
  if(source.size()<=128 && std::none_of(source.begin(),source.end(),[](unsigned char c){return (c>='A'&&c<='Z')||(c>='a'&&c<='z');})) {
    for(size_t i=0;i<source.size();++i) {
      const auto c=static_cast<unsigned char>(source[i]);
      if(c==' ')continue;
      if(c==0x81 && i+1<source.size() && static_cast<unsigned char>(source[i+1])==0x40){++i;continue;}
      compact+=source[i];
      if(((c>=0x81 && c<=0x9f)||(c>=0xe0 && c<=0xfc)) && i+1<source.size())compact+=source[++i];
    }
    if(compact.size()==source.size())compact.clear();
    else if(auto it=translations.find(Fingerprint(compact));it!=translations.end())return it->second;
  }
  // A trailing space distinguishes a tie count from a duration in the native
  // record builder. Match the original format before dropping its padding.
  if(const auto translated=TranslateFormatted(source))return translated;
  if(!compact.empty())
    if(const auto translated=TranslateFormatted(compact))return translated;
  if (japanese && trace_text) {
    std::lock_guard guard(trace_mutex);
    if (traced.insert(fingerprint).second && untranslated) {
      // Hex preserves CP932 and control bytes without depending on host locale.
      constexpr char digits[]="0123456789ABCDEF";
      untranslated << std::hex << address << '\t';
      for (unsigned char byte : source) untranslated << digits[byte>>4] << digits[byte&15];
      untranslated << '\n';
      if(traced.size()%16==0)untranslated.flush();
    }
  }
  return address;
}

void RenderLocalized(PPCContext& ctx, uint8_t* base, PPCFunc* original) {
  TextProfileScope profile(TextPhase::Raster);
  struct ActiveText {
    PPCContext* previous=active_text_context;
    uint32_t address=active_text_address, object=active_text_object;
    uint32_t resized_object = 0, original_x = 0, original_width = 0, original_alignment = 0;
    ~ActiveText(){
      if (resized_object) {
        Write32(resized_object + 12, original_x);
        Write32(resized_object + 20, original_width);
        Write32(resized_object + 28, original_alignment);
      }
      active_text_context=previous;active_text_address=address;active_text_object=object;
    }
  } active;
  active_text_context=&ctx; active_text_address=ctx.r5.u32; active_text_object=ctx.r3.u32;
  if (!memory) { profile.Suspend(); original(ctx, base); return; }
  const auto caller = uint32_t(ctx.lr);
  if (romanized_announced_grid && (caller == 0x823832D0 || caller == 0x823832D8)
      && ctx.r5.u32 && ctx.r27.u32 < 10 && ctx.r30.u32 > 0 && ctx.r30.u32 <= 256) {
    const auto* glyph = memory->TranslateVirtual(ctx.r5.u32);
    if (glyph[0] == 0x82 && glyph[1] && !glyph[2]) {
      const uint16_t code = (uint16_t(glyph[0]) << 8) | glyph[1];
      if (auto it = announced_kana.find(code); it != announced_kana.end()) {
        ctx.r5.u64 = it->second;
        active.resized_object = ctx.r3.u32;
        active.original_x = Read32(ctx.r3.u32 + 12);
        active.original_width = Read32(ctx.r3.u32 + 20);
        active.original_alignment = Read32(ctx.r3.u32 + 28);
        // Fit each syllable inside the original cell before the native grid
        // advances to the next column. r27 is the native column index.
        Write32(ctx.r3.u32 + 12, ctx.r27.u32 * ctx.r30.u32);
        Write32(ctx.r3.u32 + 20, std::min(active.original_width, ctx.r30.u32));
        Write32(ctx.r3.u32 + 28, 1);
      }
    }
  }
  ctx.r5.u64 = Translate(ctx.r5.u32,false,caller);
  // The markup renderer submits spaces as individual glyph runs. The Japanese
  // raster scaler divides by the bitmap width, which is zero for ASCII space.
  // Whitespace still advances in the caller's separate measurement pass.
  if(ctx.r5.u32) {
    const auto* text=memory->TranslateVirtual(ctx.r5.u32);
    size_t i=0;
    while(i<8192 && (text[i]==' ' || text[i]=='\t' || text[i]=='\r' || text[i]=='\n'))++i;
    if(i && i<8192 && !text[i]) {ctx.r3.u64=1;return;}
  }
  const uint32_t object = ctx.r3.u32;
  if(ctx.r4.u32) {
    const auto available_width=std::bit_cast<float>(Read32(ctx.r4.u32+92))-int32_t(Read32(object+12));
    const auto available_height=std::bit_cast<float>(Read32(ctx.r4.u32+96))-int32_t(Read32(object+16));
    // Expanded English paragraphs can reach the bottom/right edge of a
    // fixed-size text surface. A zero-size scaling target is fully clipped.
    if((Read32(object+20)==0xFFFFFFFFu && available_width<=0) ||
       (Read32(object+24)==0xFFFFFFFFu && available_height<=0)) {ctx.r3.u64=1;return;}
  }
  const uint32_t alignment = Read32(object+0x1C);
  const uint32_t spacing = Read32(object+0x24);
  // The Japanese headings use justification across the whole box. Do not
  // spread Latin words across that width; retain left/center/right alignment.
  const bool latin = IsLatin(ctx.r5.u32);
  if (latin) {
    if (alignment==3) Write32(object+0x1C, 0);
    Write32(object+0x24, 0);
  }
  const auto old_cache=Read32(object+8);
  auto cache=latin?LatinCache(object):0;
  if(cache && ctx.r4.u32) {
    const auto width_limit=Read32(object+20)==0xFFFFFFFFu
      ? int(std::bit_cast<float>(Read32(ctx.r4.u32+92)))-int32_t(Read32(object+12))
      : int32_t(Read32(object+20));
    const auto* mapping=memory->TranslateVirtual(0x82895538);
    const auto* text=memory->TranslateVirtual(ctx.r5.u32);
    for(unsigned attempt=0;attempt<4 && width_limit>0;++attempt) {
      const auto height=Read32(cache+24),stride=(Read32(cache+20)/2)*height+1;
      const auto width=localization::MaxLineWidth(
          std::string_view(reinterpret_cast<const char*>(text),strnlen(reinterpret_cast<const char*>(text),8192)),
          [&](unsigned char c) {
        auto index=mapping[c==' '?unsigned('I'):c];
        if(index==255)index=0;
        return memory->TranslateVirtual(cache+28+index*stride)[0];
      });
      if(width<=uint32_t(width_limit) || height<=6)break;
      const auto smaller=GetLatinFontCache(*memory,std::max(6u,uint32_t(uint64_t(height)*width_limit/width)));
      if(!smaller)break;
      cache=smaller;
    }
  }
  if(cache) {
    Write32(object+8,cache);
    profile.Suspend();
    __imp__sub_8260EDE0(ctx,base);
    profile.Resume();
    Write32(object+8,old_cache);
  } else {
    profile.Suspend();
    original(ctx, base);
    profile.Resume();
  }
  if (latin) { Write32(object+0x1C, alignment); Write32(object+0x24, spacing); }
}
}

void ReportActiveTextTrap() {
  if(auto* ctx=active_text_context) {
    REXLOG_CRITICAL("Text trap: string={:08X}, object={:08X}, LR={:08X}, r11={:08X}, glyph-count/r22={:08X}, width/r31={:08X}",
      active_text_address,active_text_object,uint32_t(ctx->lr),ctx->r11.u32,ctx->r22.u32,ctx->r31.u32);
    if(memory) {
      REXLOG_CRITICAL("Text trap details: text={}, width={}, height={}, align={}, spacing={}, r3={}, r4={}, r29={}, r30={}",
        reinterpret_cast<const char*>(memory->TranslateVirtual(active_text_address)),
        Read32(active_text_object+20),Read32(active_text_object+24),Read32(active_text_object+28),Read32(active_text_object+36),
        ctx->r3.u32,ctx->r4.u32,ctx->r29.u32,ctx->r30.u32);
    }
  }
}

void InitializeTextLocalization(rex::Runtime& runtime) {
  const char* enabled = std::getenv("PROSPI3_ENGLISH");
  if (!enabled || std::string_view(enabled)!="1") return;
  memory = runtime.memory();
  // Standalone scoreboard/stat glyphs only. These are never substituted inside
  // a longer Japanese name or sentence submitted by the markup parser.
  for(const auto label:{"\x8f\x9f","\x95\x89","\x95\x5c","\x97\xa0","\x90\x5f","\x83\x8d"})
    short_labels.insert(Fingerprint(label));
  const auto* latin_font=std::getenv("PROSPI3_LATIN_FONT");
  latin_font_enabled=!latin_font || std::string_view(latin_font)!="0";
  REXLOG_INFO("Custom Latin font: {}",latin_font_enabled?"enabled":"disabled (diagnostic)");
  size_t bytes=0;
  for (const auto& entry : kFullTranslations) bytes += entry.english.size()+1;
  for (const auto& entry : kAnnouncedNames) bytes += entry.english.size()+1;
  for (const auto& entry : kAnnouncedKana) bytes += entry.english.size()+1;
  if (bytes > 16*1024*1024) throw std::runtime_error("Translation pool too large");
  const uint32_t pool = memory->SystemHeapAlloc(static_cast<uint32_t>(bytes));
  if (!pool) throw std::runtime_error("Cannot allocate English string pool");
  std::unordered_map<uint32_t,uint32_t> relocated;
  uint32_t position=pool;
  for (const auto& entry : kFullTranslations) {
    if(entry.address) {
      const auto* original=reinterpret_cast<const char*>(memory->TranslateVirtual(entry.address));
      if (original[entry.source_size] || Fingerprint(std::string_view(original,entry.source_size))!=entry.fingerprint)
        throw std::runtime_error("Full translation rejected: original fingerprint differs");
      if(localization::IsReportPhraseAddress(entry.address))
        report_translations.Add(std::string_view(original,entry.source_size),entry.english,
                                localization::IsReportPrefixAddress(entry.address));
      if(auto format=localization::FormatTranslation::Create(std::string_view(original,entry.source_size),entry.english))
        format_translations.push_back(std::move(*format));
      if(auto format=localization::FormatTranslation::Create(std::string_view(original,entry.source_size),entry.english,true))
        contextual_formats.emplace(entry.address,std::move(*format));
    }
    else if(!entry.format_source.empty()) {
      if(auto format=localization::FormatTranslation::Create(entry.format_source,entry.english))
        format_translations.push_back(std::move(*format));
    }
    auto* target=memory->TranslateVirtual(position);
    std::memcpy(target,entry.english.data(),entry.english.size());
    target[entry.english.size()]=0;
    translations.emplace(entry.fingerprint,position);
    if(entry.address) relocated.emplace(entry.address,position);
    position+=static_cast<uint32_t>(entry.english.size()+1);
  }
  announced_names.reserve(std::size(kAnnouncedNames));
  for (const auto& entry : kAnnouncedNames) {
    auto* target = memory->TranslateVirtual(position);
    std::memcpy(target, entry.english.data(), entry.english.size());
    target[entry.english.size()] = 0;
    announced_names.emplace(entry.source_hash, position);
    position += static_cast<uint32_t>(entry.english.size() + 1);
  }
  for (const auto& entry : kAnnouncedKana) {
    auto* target = memory->TranslateVirtual(position);
    std::memcpy(target, entry.english.data(), entry.english.size());
    target[entry.english.size()] = 0;
    announced_kana.emplace(entry.source_code, position);
    position += static_cast<uint32_t>(entry.english.size() + 1);
  }
  dynamic_pool=memory->SystemHeapAlloc(kDynamicPoolSize);
  if(!dynamic_pool)throw std::runtime_error("Cannot allocate formatted translation pool");
  REXLOG_INFO("Formatted English text: {} templates, {} bytes bounded output cache",format_translations.size(),kDynamicPoolSize);
  size_t changed=0;
  // Rewrite static string pointers, including strings consumed by higher-level
  // markup parsers. The original byte slots stay intact for direct code refs;
  // the render hooks translate those references by content fingerprint.
  // Relocating a format string can expand writes into fixed game buffers.
  // Keep this diagnostic option disabled until every writer is bounded;
  // normal English mode translates at the markup/font boundary instead.
  const char* relocate=std::getenv("PROSPI3_RELOCATE_TEXT");
  if(relocate && std::string_view(relocate)=="1")
  for (const auto [start,end] : {std::pair{0x82000400u,0x820AB20Cu},std::pair{0x826E0000u,0x82C10AD8u}}) {
    auto* heap=memory->LookupHeap(start);
    uint32_t old=0;
    if (!heap || !heap->Protect(start,end-start,rex::memory::kMemoryProtectRead|rex::memory::kMemoryProtectWrite,&old))
      throw std::runtime_error("Cannot relocate string pointers");
    for (uint32_t address=start; address+4<=end; address+=4) {
      if (const auto it=relocated.find(Read32(address));it!=relocated.end()) { Write32(address,it->second); ++changed; }
    }
    if (!heap->Protect(start,end-start,old)) throw std::runtime_error("Cannot restore section protection");
  }
  const auto* trace=std::getenv("PROSPI3_TRACE_TEXT");
  trace_text=trace && std::string_view(trace)=="1";
  if(trace_text) {
    std::filesystem::create_directories(runtime.user_data_root());
    untranslated.open(runtime.user_data_root()/"untranslated-text.tsv",std::ios::app);
    short_text.open(runtime.user_data_root()/"short-text.tsv",std::ios::app);
  }
  REXLOG_INFO("Full English text draft: {} strings, {} relocated references, {} pool bytes at {:08X}",std::size(kFullTranslations),changed,bytes,pool);
}

REX_EXTERN(sub_823825F8) {
  if (memory) {
    std::lock_guard guard(announced_grid_mutex);
    announced_grid_objects.erase(ctx.r3.u32);
    // Only the announcer selector constructs its grid at this call site.
    if (ctx.lr == 0x82383DE8) announced_grid_objects.insert(ctx.r3.u32);
  }
  __imp__sub_823825F8(ctx, base);
}

REX_EXTERN(sub_82382B10) {
  if (memory) {
    std::lock_guard guard(announced_grid_mutex);
    announced_grid_objects.erase(ctx.r3.u32);
  }
  __imp__sub_82382B10(ctx, base);
}

REX_EXTERN(sub_823831A8) {
  struct GridScope {
    bool previous = romanized_announced_grid;
    ~GridScope() { romanized_announced_grid = previous; }
  } scope;
  romanized_announced_grid = false;
  if (memory) {
    std::lock_guard guard(announced_grid_mutex);
    romanized_announced_grid = announced_grid_objects.contains(ctx.r3.u32);
  }
  __imp__sub_823831A8(ctx, base);
}

REX_EXTERN(sub_82135D68) {
  switch (ctx.lr) {
    case 0x82383EA0:
    case 0x82383F98:
    case 0x82384020:
    case 0x8238411C:
    case 0x823842FC:
    case 0x8238433C:
    case 0x82384AE4:
      if (memory && ctx.r5.u32) {
        // These callers pass the selected name from EDIT.CHK to the renderer.
        // The kana search grid and the voice ID still use the native records.
        const auto* name = reinterpret_cast<const char*>(memory->TranslateVirtual(ctx.r5.u32));
        constexpr size_t kMaxNameBytes = 16;
        const auto length = strnlen(name, kMaxNameBytes);
        if (length < kMaxNameBytes) {
          if (auto it = announced_names.find(Fingerprint({name, length}));
              it != announced_names.end()) {
            ctx.r5.u64 = it->second;
          }
        }
      }
      break;
  }
  __imp__sub_82135D68(ctx, base);
}

REX_EXTERN(sub_8262FB40) {
  const auto destination = ctx.r3.u32;
  const bool save_title = memory && ctx.lr == 0x826123EC && ctx.r4.u32 == 0x820A6F94;
  __imp__sub_8262FB40(ctx, base);
  if (!save_title) return;

  // This caller copies the default title into XCONTENT_DATA's 128-unit
  // UTF-16BE display field. The file name used to open the save is separate.
  using rex::system::xam::XCONTENT_DATA;
  auto* content = reinterpret_cast<XCONTENT_DATA*>(
      memory->TranslateVirtual(destination - offsetof(XCONTENT_DATA, display_name_raw)));
  constexpr uint8_t original_title[] = {
      0x30, 0xD7, 0x30, 0xED, 0x91, 0xCE, 0x74, 0x03, 0x30, 0xB9,
      0x30, 0xD4, 0x30, 0xEA, 0x30, 0xC3, 0x30, 0xC4, 0xFF, 0x13, 0, 0,
  };
  if (std::memcmp(content->display_name_raw.uint, original_title, sizeof(original_title)) == 0) {
    content->set_display_name(u"Pro Yakyuu Spirits 3");
  }
}

REX_EXTERN(sub_8260E870) { RenderLocalized(ctx,base,__imp__sub_8260E870); }
REX_EXTERN(sub_8260EDE0) { RenderLocalized(ctx,base,__imp__sub_8260EDE0); }
REX_EXTERN(sub_8260D8B0) {
  TextProfileScope profile(TextPhase::Measure);
  if(memory && ctx.r4.u32) {
    const auto* text=memory->TranslateVirtual(ctx.r4.u32);
    // Measure whole labels with the same English glyph cache used to draw them.
    // Preserve isolated Japanese glyph measurements inside unknown prose/names.
    if(!(text[0]>=0x80 && text[1] && !text[2]))
      ctx.r4.u64=Translate(ctx.r4.u32,false,uint32_t(ctx.lr));
  }
  if(!memory || !IsLatin(ctx.r4.u32)) {profile.Suspend();__imp__sub_8260D8B0(ctx,base);return;}
  const auto object=ctx.r3.u32, cache=LatinCache(object);
  if(!cache){profile.Suspend();__imp__sub_8260D8B0(ctx,base);return;}
  const auto japanese=Read32(object+4),latin=Read32(object+8);
  Write32(object+4,0);Write32(object+8,cache);
  profile.Suspend();
  __imp__sub_8260D8B0(ctx,base);
  profile.Resume();
  Write32(object+4,japanese);Write32(object+8,latin);
}
REX_EXTERN(sub_82413358) {
  TextProfileScope profile(TextPhase::Markup);
  if(memory)ctx.r4.u64=Translate(ctx.r4.u32,true);
  profile.Suspend();
  __imp__sub_82413358(ctx,base);
}

REX_EXTERN(sub_82548958) {
  // The native play builder uses the same bases-loaded label as the recap's
  // situation line. Only a home run inside this builder is a grand slam.
  struct PlayScope {
    std::optional<uint32_t> previous;
    ~PlayScope() { scoring_play_runs = previous; }
  } scope{scoring_play_runs};
  scoring_play_runs = ctx.r5.u32;
  __imp__sub_82548958(ctx,base);
}

REX_EXTERN(sub_8254C0A8) {
  if(memory && ctx.r8.u32) {
    const auto caller=uint32_t(ctx.lr);
    const auto address=ctx.r8.u32;
    uint32_t translated=0;
    if(caller==0x8254B788 || caller==0x8254BACC) {
      // Both speaker builders terminate their name and suffix in a 32-byte slot.
      const auto* text=reinterpret_cast<const char*>(memory->TranslateVirtual(address));
      const auto length=strnlen(text,32);
      if(length<32)translated=TranslateFormatted(std::string_view(text,length),true);
    }
    // Translate the entire line before the native routine splits it into glyphs.
    ctx.r8.u64=translated ? translated : Translate(address,true,caller);
  }
  __imp__sub_8254C0A8(ctx,base);
}

REX_EXTERN(sub_8260F470) {
  if(memory && latin_font_enabled && ctx.lr==0x8254C0F4 && IsLatin(ctx.r5.u32)) {
    // Career rows use one Japanese cell per character. Draw an English row
    // as a whole so the Latin font can measure and fit it proportionally.
    auto* renderer=Read32(ctx.r3.u32+4) ? __imp__sub_8260E870 : __imp__sub_8260EDE0;
    RenderLocalized(ctx,base,renderer);
    ctx.r3.u64=1;
    return;
  }
  __imp__sub_8260F470(ctx,base);
}

// These two report builders format into known 128/1024-byte stack arrays,
// then apply their own 127/1023-byte destination bounds. Translate the completed
// piece before it is appended and wrapped; never expand the printf format.
REX_EXTERN(sub_826BA910) {
  const auto caller=uint32_t(ctx.lr),destination=ctx.r3.u32,format_address=ctx.r4.u32;
  __imp__sub_826BA910(ctx,base);
  if(!memory || (caller!=0x82548E50 && caller!=0x82548F68))return;
  const size_t capacity=caller==0x82548E50?128:1024;
  const auto* original=reinterpret_cast<const char*>(memory->TranslateVirtual(destination));
  const size_t original_length=strnlen(original,capacity);
  if(original_length==capacity)return;
  const std::string_view source(original,original_length);
  auto contextual=localization::RecapPieceOverride(format_address,source,scoring_play_runs);
  if(!contextual) {
    if(auto it=contextual_formats.find(format_address);it!=contextual_formats.end()) {
      contextual=it->second.Apply(source,[](std::string_view capture) {
        if(auto found=translations.find(Fingerprint(capture));found!=translations.end())
          return std::string(reinterpret_cast<const char*>(memory->TranslateVirtual(found->second)));
        return std::string(capture);
      });
    }
  }
  const auto translated=contextual?destination:Translate(destination,true,caller);
  if(!contextual && translated==destination)return;
  const auto* text=contextual?contextual->c_str():reinterpret_cast<const char*>(memory->TranslateVirtual(translated));
  const size_t length=std::strlen(text);
  const bool base_situation=!scoring_play_runs &&
      (format_address==0x82099B18 || (format_address>=0x82099C9C && format_address<=0x82099CF0));
  const bool space=length && text[length-1]!=' ' && text[length-1]!='\n' &&
                   localization::RecapPieceAllowsTrailingSpace(format_address);
  const size_t output_size=length+size_t(base_situation)+size_t(space);
  if(output_size+1>capacity)return;
  auto* output=memory->TranslateVirtual(destination);
  std::memcpy(output,text,length);
  if(base_situation)output[length]='.';
  if(space)output[output_size-1]=' ';
  output[output_size]=0;
  ctx.r3.s64=int64_t(output_size);
}

// The text object sizes its sprite array using the original Japanese string.
// Expanded English needs more character quads. Grow only the three text-object
// factory call sites, using the original allocator/constructor/destructor.
REX_EXTERN(sub_825DEAC8) {
  const auto caller=uint32_t(ctx.lr),original=ctx.r3.u32;
  const bool text_pool=memory && original && original<=2048 &&
    (caller==0x82412C24 || caller==0x82413288 || caller==0x82413318);
  if(text_pool)ctx.r3.u64=std::max(256u,original*4);
  __imp__sub_825DEAC8(ctx,base);
  if(text_pool && ctx.r3.u32) {
    std::lock_guard guard(quad_mutex);
    quad_capacities[ctx.r3.u32]={original,false};
    REXLOG_INFO("English text quad capacity: object={:08X}, original={}, expanded={}, caller={:08X}",ctx.r3.u32,original,Read32(ctx.r3.u32+404),caller);
  }
}
REX_EXTERN(sub_825DF6A8) {
  const auto object=ctx.r3.u32,caller=uint32_t(ctx.lr);
  __imp__sub_825DF6A8(ctx,base);
  if(!memory || (caller!=0x82413534 && caller!=0x824138CC))return;
  if(ctx.r3.u32==0xFFFFFFFFu) {
    REXLOG_CRITICAL("Text quad array exhausted before unchecked index use: object={:08X}, capacity={}, caller={:08X}",object,Read32(object+404),caller);
    WritePerformanceReport();
    throw std::runtime_error("Text quad capacity exhausted");
  }
  std::lock_guard guard(quad_mutex);
  if(auto it=quad_capacities.find(object);it!=quad_capacities.end() && !it->second.exceeded && ctx.r3.u32>=it->second.original) {
    it->second.exceeded=true;
    REXLOG_INFO("English text used additional quad: object={:08X}, original capacity={}, index={}",object,it->second.original,ctx.r3.u32);
  }
}
