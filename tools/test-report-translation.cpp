#include "../prospi3-recomp/src/report_translation.h"
#include "../prospi3-recomp/generated/translation/full_text.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
#include <unordered_map>

int main(int argc,char** argv) {
  if(argc!=2)return 2;
  std::ifstream file(argv[1],std::ios::binary);
  const std::string image((std::istreambuf_iterator<char>(file)),{});
  localization::ReportTranslation reports;
  std::unordered_map<uint32_t,std::string> source;
  for(const auto& row:kFullTranslations) {
    if(!row.address || !localization::IsReportPhraseAddress(row.address))continue;
    const size_t offset=row.address-0x82000000;
    if(offset+row.source_size>=image.size())return 3;
    source[row.address]=image.substr(offset,row.source_size);
    uint64_t fingerprint=0xcbf29ce484222325ULL;
    for(unsigned char c:source[row.address])fingerprint=(fingerprint^c)*0x100000001b3ULL;
    if(fingerprint!=row.fingerprint)return 4;
    reports.Add(source[row.address],row.english,
                localization::IsReportPrefixAddress(row.address));
  }
  auto join=[&](std::initializer_list<uint32_t> addresses) {
    std::string text;
    for(auto address:addresses){assert(source.contains(address));text+=source.at(address);}
    return text;
  };
  // Assemble the same phrase groups selected by the native report table.
  const auto steady=join({0x82093640,0x82093628,0x820934B8,0x82093478,0x82093230});
  assert(reports.Apply(steady)==
      "This season: as a starter, he pitched steadily. Contributes to the team.");
  const auto unlucky=join({0x8206D148,0x8209360C,0x820934E0,0x82093484});
  assert(reports.Apply(unlucky)==
      "Last season: as a reliever, he pitched reliably. However, bad luck hurt the final results.");
  const auto batter=join({0x82093648,0x82092E10});
  assert(reports.Apply(batter)==
      "In the first half: Helps the team win through outstanding athleticism.");
  const auto coach=join({0x82093D30,0x82092208,0x82092548});
  assert(reports.Apply(coach)=="Assessment: A dependable pitcher who supports the team.");
  const auto full=steady+join({0x8209319C,0x820937F0,0x82093060,
                              0x82093038,0x82093694,0x82092FB8});
  assert(reports.Apply(full)==
      "This season: as a starter, he pitched steadily. Contributes to the team. "
      "Above all, Outstanding Control is beyond reproach. "
      "A minor concern: Poor Control needs improvement.");
  assert(!reports.Apply(steady+"unrecognized text"));
  assert(!reports.Apply(source.at(0x820934B8))); // A phrase alone is not a report.
  assert(!reports.Apply(steady,1));
  using localization::RecapPieceAllowsTrailingSpace;
  using localization::RecapPieceOverride;
  assert(RecapPieceOverride(0x8209988C,"1/3")=="and 1/3");
  assert(RecapPieceOverride(0x8208DF10,"") == ".");
  assert(RecapPieceOverride(0x82099A08,"") == "");
  assert(!RecapPieceOverride(0x82099B18,""));
  assert(RecapPieceOverride(0x82099B18,"",4) == "Grand Slam");
  assert(RecapPieceOverride(0x82099B20,"",4) == "");
  assert(!RecapPieceOverride(0x82099B20,"",3));
  assert(!RecapPieceAllowsTrailingSpace(0x820997EC));
  assert(!RecapPieceAllowsTrailingSpace(0x820997F8));
  std::cout<<"Native report phrase checks passed\n";
}
