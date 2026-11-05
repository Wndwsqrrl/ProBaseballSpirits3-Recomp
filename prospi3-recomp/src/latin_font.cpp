#include "latin_font.h"
#include <rex/system/xmemory.h>
#include <rex/logging.h>
#include <algorithm>
#include <cstring>
#include <mutex>
#include <unordered_map>
#include <vector>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>
#endif

uint32_t GetLatinFontCache(rex::memory::Memory& memory, uint32_t height) {
#ifdef _WIN32
  if(height<6 || height>128)return 0;
  static std::mutex mutex;
  static std::unordered_map<uint32_t,uint32_t> caches;
  std::lock_guard guard(mutex);
  if(auto it=caches.find(height);it!=caches.end())return it->second;
  const auto dc=CreateCompatibleDC(nullptr);
  if(!dc)return 0;
  const auto font=CreateFontW(int(height),0,0,0,FW_NORMAL,FALSE,FALSE,FALSE,ANSI_CHARSET,
    OUT_TT_PRECIS,CLIP_DEFAULT_PRECIS,ANTIALIASED_QUALITY,DEFAULT_PITCH,L"Arial");
  if(!font){DeleteDC(dc);return 0;}
  const auto previous=SelectObject(dc,font);
  TEXTMETRICW metrics{};
  GetTextMetricsW(dc,&metrics);
  const uint32_t width=height*2, row_bytes=width/2, stride=row_bytes*height+1;
  // The game initializes this map from its printable ASCII character order.
  const auto* mapping=memory.TranslateVirtual(0x82895538);
  uint32_t slots=1;
  for(unsigned ch=33;ch<=126;++ch)if(mapping[ch]!=255)slots=std::max(slots,uint32_t(mapping[ch])+1);
  std::vector<uint8_t> data(28+slots*stride,0);
  auto put32=[&](size_t at,uint32_t value){data[at]=uint8_t(value>>24);data[at+1]=uint8_t(value>>16);data[at+2]=uint8_t(value>>8);data[at+3]=uint8_t(value);};
  put32(20,width); put32(24,height);
  MAT2 transform{};transform.eM11.value=1;transform.eM22.value=1;
  for(unsigned ch=33;ch<=126;++ch) {
    if(mapping[ch]==255)continue;
    GLYPHMETRICS glyph{};
    const auto bytes=GetGlyphOutlineW(dc,ch,GGO_GRAY8_BITMAP,&glyph,0,nullptr,&transform);
    auto* record=data.data()+28+mapping[ch]*stride;
    record[0]=uint8_t(std::clamp<int>(glyph.gmCellIncX,1,int(width)));
    if(bytes==GDI_ERROR || !bytes)continue;
    std::vector<uint8_t> pixels(bytes);
    if(GetGlyphOutlineW(dc,ch,GGO_GRAY8_BITMAP,&glyph,bytes,pixels.data(),&transform)==GDI_ERROR)continue;
    const auto source_pitch=(glyph.gmBlackBoxX+3)&~3u;
    for(uint32_t y=0;y<glyph.gmBlackBoxY;++y)for(uint32_t x=0;x<glyph.gmBlackBoxX;++x) {
      const int dest_x=int(x)+glyph.gmptGlyphOrigin.x;
      const int dest_y=int(y)+metrics.tmAscent-glyph.gmptGlyphOrigin.y;
      if(dest_x<0 || dest_y<0 || dest_x>=int(width) || dest_y>=int(height))continue;
      const uint8_t coverage=uint8_t(std::min(15u,(unsigned(pixels[y*source_pitch+x])*15+32)/64));
      // The guest stores the left pixel in the low nibble.
      record[1+dest_y*row_bytes+dest_x/2]|=uint8_t(coverage<<((dest_x&1)*4));
    }
  }
  SelectObject(dc,previous);DeleteObject(font);DeleteDC(dc);
  const auto address=memory.SystemHeapAlloc(uint32_t(data.size()));
  if(!address)return 0;
  std::memcpy(memory.TranslateVirtual(address),data.data(),data.size());
  caches.emplace(height,address);
  REXLOG_INFO("Created proportional Latin font cache: address={:08X}, height={}, slots={}, bytes={}",address,height,slots,data.size());
  return address;
#else
  return 0;
#endif
}
