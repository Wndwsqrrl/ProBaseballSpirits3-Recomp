#include "../prospi3-recomp/src/format_translation.h"
#include "../prospi3-recomp/src/offseason_text.h"
#include "../prospi3-recomp/src/text_layout.h"
#include "../prospi3-recomp/src/report_translation.h"
#include <cassert>
#include <iostream>

int main() {
  using localization::FormatTranslation;
  using localization::PrepareOffseasonMessage;
  const auto offseason=PrepareOffseasonMessage("100% Stars passed.\n(\vPicks left: 2\v)\nNext selection.");
  assert(offseason=="100%% Stars passed.\n(\vPicks left: 2\v)\nNext selection.");
  assert(PrepareOffseasonMessage(std::string(32,'A')+"\nNext.").has_value());
  assert(!PrepareOffseasonMessage(std::string(32,'A')+"\v\nNext."));
  assert(!PrepareOffseasonMessage(std::string(33,'A')));
  assert(!PrepareOffseasonMessage("One\nTwo\nThree\nFour"));
  assert(!PrepareOffseasonMessage("One\n\nThree"));
  assert(!PrepareOffseasonMessage("\x8f\x9f"));
  assert(localization::NormalizeFullwidthAscii("Igawa\x81\x40Kei")=="Igawa Kei");
  assert(localization::NormalizeFullwidthAscii("\x82\x50\x82\x51\x82\x51\x81\x44\x82\x4f\x82\x8d")=="122.0m");
  assert(!localization::NormalizeFullwidthAscii("\x8f\x9f"));
  assert(!localization::NormalizeFullwidthAscii("\x82"));
  const auto identity=[](std::string_view s){return std::string(s);};
  // Bytes deliberately resemble CP932 so tests exercise the actual byte parser.
  const std::string wins="\x8f\x9f",losses="\x94\x73",saves="\x82\x72";
  auto stats=FormatTranslation::Create("%d"+wins+"%d"+losses+"%d"+saves,"%d W / %d L / %d SV");
  assert(stats && stats->Apply("5"+wins+"4"+losses+"27"+saves,identity)=="5 W / 4 L / 27 SV");
  auto fullwidth=FormatTranslation::Create("%d"+wins,"%d W");
  assert(fullwidth && fullwidth->Apply("\x82\x50\x82\x52"+wins,identity)=="13 W");
  assert(!stats->Apply("5"+wins+"4"+losses,identity));
  assert(!stats->Apply("bad"+wins+"4"+losses+"27"+saves,identity));
  assert(!stats->Apply("5"+wins+"4"+losses+"27"+saves+"x",identity));
  auto name=FormatTranslation::Create("%s"+wins+losses,"Player: %s");
  assert(name && name->Apply("Igawa"+wins+losses,identity)=="Player: Igawa");
  assert(name->Apply("\x81\x40 Igawa Kei \x81\x40"+wins+losses,identity)=="Player: Igawa Kei");
  assert(name->Apply(wins+wins+losses,[&](std::string_view s){return s==wins?"Igawa":std::string(s);})=="Player: Igawa");
  assert(name->Apply("\x81\x40"+wins+" \x81\x40"+wins+losses,
      [&](std::string_view s){return s==wins?"Igawa":std::string(s);})=="Player: Igawa");
  assert(!FormatTranslation::Create("%s"+wins,"%s")); // Too broad: one particle.
  auto contextual=FormatTranslation::Create("%s"+wins,"%s:",true);
  assert(contextual && contextual->Apply("Igawa"+wins,identity)=="Igawa:");
  assert(!FormatTranslation::Create("%s%d"+wins+losses,"%s %d")); // Ambiguous adjacent slots.
  assert(!FormatTranslation::Create("%n"+wins+losses,"%n"));
  assert(!FormatTranslation::Create("%*d"+wins+losses,"%*d"));
  assert(!FormatTranslation::Create("%d"+wins+losses,"%s"));
  auto escaped=FormatTranslation::Create("%2d%%"+wins+losses,"%2d percent");
  assert(escaped && escaped->Apply(" 7%"+wins+losses,identity)==" 7 percent");
  assert(!name->Apply(std::string(1025,'a'),identity));
  auto repeated=FormatTranslation::Create("%s"+wins+"%s"+losses,"%s / %s");
  assert(repeated && !repeated->Apply(std::string(1024,'a'),identity));
  // Six changing fields occur in mission stat summaries.
  auto summary=FormatTranslation::Create(wins+losses+"%d G %d PA %d H %s AVG %d RBI %d HR",
                                        "%d G, %d PA, %d H, %s AVG, %d RBI, %d HR");
  assert(summary && summary->Apply(wins+losses+"3 G 12 PA 4 H .333 AVG 2 RBI 1 HR",identity)==
      "3 G, 12 PA, 4 H, .333 AVG, 2 RBI, 1 HR");
  assert(!FormatTranslation::Create(wins+"%d|%d|%d|%d|%d|%d|%d|%d|%d",
                                       "%d|%d|%d|%d|%d|%d|%d|%d|%d"));
  auto advance=[](unsigned char c){return c=='W'?3u:1u;};
  assert(localization::MaxLineWidth("Title\nWWWW",advance)==12);
  assert(localization::MaxLineWidth("WWWW\r\nx",advance)==12);
  assert(localization::MaxLineWidth("",advance)==0);
  localization::ReportTranslation report;
  report.Add(wins,"This season, ");
  report.Add(wins,"This season, ",true);
  report.Add(losses,"as a starter, ");
  report.Add(saves,"he pitched well. ");
  assert(report.Apply(wins+losses+saves)=="This season, as a starter, he pitched well.");
  assert(!report.Apply(losses+saves)); // No recognized report prefix.
  assert(!report.Apply(wins+"unknown")); // Never translate a partial match.
  assert(!report.Apply(wins+std::string(1024,' ')));
  assert(!report.Apply(wins+losses+saves,1));
  report.Add(wins+losses,"A conflicting interpretation. ");
  assert(!report.Apply(wins+losses+saves));
  std::cout<<"Formatted translation safety checks passed\n";
}
