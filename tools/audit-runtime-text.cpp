// Offline coverage audit using real renderer traces and the original loaded image.
#include "../prospi3-recomp/src/format_translation.h"
#include "../prospi3-recomp/generated/translation/full_text.h"
#include <fstream>
#include <iostream>
#include <iterator>
#include <unordered_map>
#include <unordered_set>
uint64_t Hash(std::string_view s) {
  uint64_t h=0xcbf29ce484222325ULL;for(unsigned char c:s)h=(h^c)*0x100000001b3ULL;return h;
}
std::string Hex(std::string_view s) {
  std::string r;const char* digits="0123456789abcdef";
  for(unsigned char c:s){r+=digits[c>>4];r+=digits[c&15];}return r;
}
int main(int argc,char** argv) {
  if(argc!=3)return 2;
  std::ifstream input(argv[1],std::ios::binary);
  std::string image((std::istreambuf_iterator<char>(input)),{});
  std::unordered_map<uint64_t,std::string> exact;
  std::vector<localization::FormatTranslation> formats;
  for(const auto& row:kFullTranslations) {
    exact.emplace(row.fingerprint,row.english);
    std::string_view source=row.format_source;
    if(row.address) {
      const size_t offset=row.address-0x82000000;
      if(offset+row.source_size>=image.size())return 3;
      source=std::string_view(image).substr(offset,row.source_size);
      if(Hash(source)!=row.fingerprint)return 4;
    }
    if(auto format=localization::FormatTranslation::Create(source,row.english))formats.push_back(*format);
  }
  std::cerr<<formats.size()<<" supported runtime templates\n";
  std::ifstream trace(argv[2]);std::unordered_set<std::string> seen;std::string line;
  for(;std::getline(trace,line);) {
    const auto tab=line.find('\t');if(tab==std::string::npos)continue;
    std::string source;
    for(size_t i=tab+1;i+1<line.size() && std::isxdigit(static_cast<unsigned char>(line[i]));i+=2)
      source+=char(std::stoul(line.substr(i,2),nullptr,16));
    if(!seen.insert(source).second)continue;
    std::optional<std::string> result;std::string status="unknown";
    auto trimmed=std::string_view(source);
    while(!trimmed.empty() && trimmed.front()==' ')trimmed.remove_prefix(1);
    while(!trimmed.empty() && trimmed.back()==' ')trimmed.remove_suffix(1);
    if(auto it=exact.find(Hash(trimmed));it!=exact.end()){result=it->second;status="exact";}
    else {
      result=localization::NormalizeFullwidthAscii(source);
      for(const auto& format:formats) {
        auto candidate=format.Apply(source,[&](std::string_view s){
          auto found=exact.find(Hash(s));return found==exact.end()?std::string(s):found->second;
        });
        if(!candidate)continue;
        if(result && result!=candidate){result.reset();status="ambiguous";break;}
        result=candidate;
      }
      if(result)status="formatted";
    }
    std::cout<<Hex(source)<<'\t'<<status<<'\t'<<(result?Hex(*result):"")<<'\n';
  }
}
