#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace localization {
inline bool IsReportPrefixAddress(uint32_t address) {
  return address==0x8206D148 || address==0x82093640 ||
         address==0x82093648 || address==0x82093654 || address==0x82093D30;
}
inline bool IsReportPhraseAddress(uint32_t address) {
  return IsReportPrefixAddress(address) ||
         (address>=0x82091A70 && address<0x82093A70);
}

// These fragments have no standalone English equivalent in the recap.
inline std::optional<std::string> RecapPieceOverride(uint32_t address, std::string_view original,
                                                      std::optional<uint32_t> scoring_play_runs = {}) {
  if (scoring_play_runs) {
    if (address == 0x82099B18) return "Grand Slam";
    if (address == 0x82099B20 && *scoring_play_runs == 4) return std::string{};
    if (address == 0x82066BB0) return "Strikeout";
  }
  switch (address) {
    case 0x8209988C: return "and " + std::string(original); // Fractional innings.
    case 0x8208DF10: return "."; // Sentence terminator.
    case 0x82099A58: // Fielding position already precedes the play.
    case 0x82099A08: return std::string{}; // Previous clause is already a full sentence.
    default: return std::nullopt;
  }
}

inline bool RecapPieceAllowsTrailingSpace(uint32_t address) {
  // A period or a continuation with its own space follows either batting phrase.
  return address != 0x820997EC && address != 0x820997F8;
}

// The assessment builders concatenate strings from a verified phrase table.
// Translate only complete, uniquely recognized sequences with a report prefix.
class ReportTranslation {
  struct Phrase {std::string source,english;};
  std::array<std::vector<Phrase>,256> phrases_;
  std::vector<std::string> prefixes_;
public:
  void Add(std::string_view source,std::string_view english,bool prefix=false) {
    if(source.empty() || source.size()>512 || english.size()>8192 ||
       source.find_first_of("%<")!=std::string_view::npos)return;
    for(unsigned char c:english)if(c>=128 || !c)return;
    if(prefix) {
      bool present=false;
      for(const auto& value:prefixes_)present|=value==source;
      if(!present)prefixes_.emplace_back(source);
    }
    auto& bucket=phrases_[static_cast<unsigned char>(source.front())];
    for(const auto& phrase:bucket)
      if(phrase.source==source && phrase.english==english)return;
    bucket.push_back({std::string(source),std::string(english)});
  }

  std::optional<std::string> Apply(std::string_view input,unsigned budget=4096) const {
    if(input.empty() || input.size()>1024)return {};
    bool accepted=false;
    for(const auto& prefix:prefixes_)accepted|=input.starts_with(prefix);
    if(!accepted)return {};
    struct State {std::optional<std::string> text;bool ambiguous=false;};
    std::vector<State> states(input.size()+1);
    states[0].text=std::string();
    auto advance=[&](size_t position,size_t bytes,std::string_view english) {
      auto& target=states[position+bytes];
      std::string text=*states[position].text;
      if(!text.empty() && !english.empty() &&
         std::string_view(".,!?;:").find(text.back())!=std::string_view::npos &&
         ((english.front()>='A' && english.front()<='Z') ||
          (english.front()>='a' && english.front()<='z')))text+=' ';
      text+=english;
      if(text.size()>8192)return false;
      if(!target.text)target.text=std::move(text);
      else if(*target.text!=text)target.ambiguous=true;
      target.ambiguous|=states[position].ambiguous;
      return true;
    };
    for(size_t at=0;at<input.size();++at) {
      if(!states[at].text)continue;
      const auto c=static_cast<unsigned char>(input[at]);
      if(c==' ' || c=='\r' || c=='\n') {
        if(!budget)return {};
        --budget;
        if(!advance(at,1,input.substr(at,1)))return {};
      }
      for(const auto& phrase:phrases_[c]) {
        if(!budget)return {};
        --budget;
        if(!input.substr(at).starts_with(phrase.source))continue;
        if(!advance(at,phrase.source.size(),phrase.english))return {};
      }
    }
    const auto& result=states.back();
    if(!result.text || result.ambiguous)return {};
    std::string clean;
    for(char c:*result.text) {
      if(c==' ' && (clean.empty() || clean.back()==' '))continue;
      clean+=c;
    }
    while(!clean.empty() && clean.back()==' ')clean.pop_back();
    return clean;
  }
};
}
