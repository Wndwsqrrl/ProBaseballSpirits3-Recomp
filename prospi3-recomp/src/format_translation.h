#pragma once
#include <algorithm>
#include <cctype>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

// Match text AFTER the game's printf has run. Never pass expanded English
// format strings to the game's fixed-size destination buffers.
namespace localization {
// Only convert a run when every non-ASCII character is fullwidth ASCII.
// This handles changing distances/stat numbers without changing Japanese prose.
inline std::optional<std::string> NormalizeFullwidthAscii(std::string_view input) {
  static constexpr unsigned short mapping[]={
  0x8149,0xeefc,0x8194,0x8190,0x8193,0x8195,0xeefb,0x8169,0x816a,0x8196,0x817b,0x8143,
  0x817c,0x8144,0x815e,0x824f,0x8250,0x8251,0x8252,0x8253,0x8254,0x8255,0x8256,0x8257,
  0x8258,0x8146,0x8147,0x8183,0x8181,0x8184,0x8148,0x8197,0x8260,0x8261,0x8262,0x8263,
  0x8264,0x8265,0x8266,0x8267,0x8268,0x8269,0x826a,0x826b,0x826c,0x826d,0x826e,0x826f,
  0x8270,0x8271,0x8272,0x8273,0x8274,0x8275,0x8276,0x8277,0x8278,0x8279,0x816d,0x815f,
  0x816e,0x814f,0x8151,0x814d,0x8281,0x8282,0x8283,0x8284,0x8285,0x8286,0x8287,0x8288,
  0x8289,0x828a,0x828b,0x828c,0x828d,0x828e,0x828f,0x8290,0x8291,0x8292,0x8293,0x8294,
  0x8295,0x8296,0x8297,0x8298,0x8299,0x829a,0x816f,0x8162,0x8170,0x8160,
  };
  std::string result;
  bool changed=false;
  for(size_t i=0;i<input.size();++i) {
    const auto c=static_cast<unsigned char>(input[i]);
    if(c<0x80){result+=char(c);continue;}
    if(i+1==input.size())return {};
    const auto code=(unsigned(c)<<8)|static_cast<unsigned char>(input[++i]);
    if(code==0x8140){result+=' ';changed=true;continue;} // Fullwidth name separator.
    const auto found=std::find(std::begin(mapping),std::end(mapping),code);
    if(found==std::end(mapping))return {};
    result+=char(0x21+(found-std::begin(mapping)));changed=true;
  }
  if(!changed)return {};
  return result;
}
struct FormatParts {
  std::vector<std::string> literals;
  std::vector<char> types;
};
inline std::optional<FormatParts> ParseFormat(std::string_view text) {
  FormatParts result;
  result.literals.emplace_back();
  for(size_t i=0;i<text.size();) {
    if(text[i]!='%') {result.literals.back()+=text[i++];continue;}
    if(i+1==text.size()){result.literals.back()+='%';++i;continue;}
    if(i+1<text.size() && text[i+1]=='%') {result.literals.back()+='%';i+=2;continue;}
    ++i;
    while(i<text.size() && std::string_view("-+ #0").find(text[i])!=std::string_view::npos)++i;
    while(i<text.size() && std::isdigit(static_cast<unsigned char>(text[i])))++i;
    if(i<text.size() && text[i]=='.') {
      ++i;while(i<text.size() && std::isdigit(static_cast<unsigned char>(text[i])))++i;
    }
    if(i==text.size() || std::string_view("diuoxXfFeEgGs").find(text[i])==std::string_view::npos)return {};
    if(result.types.size()==4)return {};
    result.types.push_back(text[i++]);result.literals.emplace_back();
  }
  return result;
}
inline bool ValidCapture(std::string_view value,char type) {
  if(type=='s')return value.size()<=512 && value.find_first_of("\r\n<>")==std::string_view::npos;
  const auto normalized=NormalizeFullwidthAscii(value);
  if(normalized)value=*normalized;
  while(!value.empty() && value.front()==' ')value.remove_prefix(1);
  while(!value.empty() && value.back()==' ')value.remove_suffix(1);
  if(value.empty())return false;
  if(value.front()=='+' || value.front()=='-')value.remove_prefix(1);
  bool digit=false;
  for(unsigned char c:value) {
    if(c>='0' && c<='9'){digit=true;continue;}
    if((type=='x'||type=='X') && ((c>='a'&&c<='f')||(c>='A'&&c<='F')||c=='x'||c=='X'))continue;
    if(std::string_view("fFeEgG").find(type)!=std::string_view::npos && (c=='.'||c=='e'||c=='E'||c=='+'||c=='-'))continue;
    return false;
  }
  return digit;
}
inline bool MatchSlots(const FormatParts& format,std::string_view input,size_t slot,size_t position,
                       std::vector<std::string_view>& captures,unsigned& budget) {
  if(!budget)return false;
  --budget;
  const auto& literal=format.literals[slot];
  if(!input.substr(position).starts_with(literal))return false;
  position+=literal.size();
  if(slot==format.types.size())return position==input.size();
  const auto& next=format.literals[slot+1];
  const auto limit=std::min(input.size(),position+(format.types[slot]=='s'?512u:64u));
  for(size_t end=position;end<=limit;++end) {
    if(!budget)return false;
    --budget;
    // A CP932 trail byte can look like ASCII. Only split at character boundaries.
    if(end>position) {
      const unsigned char previous=input[end-1];
      if((previous>=0x81 && previous<=0x9f)||(previous>=0xe0 && previous<=0xfc)) {
        // Count boundaries from the beginning, rather than treating every high byte as a lead.
        size_t boundary=position;
        while(boundary<end) {
          unsigned char c=input[boundary];boundary+=((c>=0x81&&c<=0x9f)||(c>=0xe0&&c<=0xfc))?2:1;
        }
        if(boundary!=end)continue;
      }
    }
    if(!next.empty() && !input.substr(end).starts_with(next))continue;
    const auto value=input.substr(position,end-position);
    if(!ValidCapture(value,format.types[slot]))continue;
    captures.push_back(value);
    if(MatchSlots(format,input,slot+1,end,captures,budget))return true;
    captures.pop_back();
  }
  return false;
}
struct FormatTranslation {
  FormatParts source,english;
  static std::optional<FormatTranslation> Create(std::string_view original,std::string_view translated,bool exact_context=false) {
    auto source=ParseFormat(original),english=ParseFormat(translated);
    if(!source || !english || source->types.empty() || source->types!=english->types)return {};
    size_t japanese_characters=0;
    for(const auto& literal:source->literals)for(size_t i=0;i<literal.size();++i) {
      const unsigned char c=literal[i];
      if(c>=0x80)++japanese_characters;
      if((c>=0x81 && c<=0x9f)||(c>=0xe0 && c<=0xfc))++i;
    }
    // Reject very broad patterns such as "%s [single Japanese particle]".
    const bool has_string=std::find(source->types.begin(),source->types.end(),'s')!=source->types.end();
    if(japanese_characters<(has_string && !exact_context?2u:1u))return {};
    for(size_t i=1;i<source->types.size();++i)if(source->literals[i].empty())return {};
    return FormatTranslation{std::move(*source),std::move(*english)};
  }
  template<class TranslateCapture>
  std::optional<std::string> Apply(std::string_view input,TranslateCapture translate) const {
    if(input.size()>1024)return {};
    std::vector<std::string_view> captures;unsigned budget=4096;
    if(!MatchSlots(source,input,0,0,captures,budget))return {};
    std::string result=english.literals[0];
    for(size_t i=0;i<captures.size();++i) {
      if(source.types[i]=='s')result+=translate(captures[i]);
      else if(auto normalized=NormalizeFullwidthAscii(captures[i]))result+=*normalized;
      else result+=captures[i];
      result+=english.literals[i+1];
    }
    if(result.size()>8192)return {};
    return result;
  }
};
}
