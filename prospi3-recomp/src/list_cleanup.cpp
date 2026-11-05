#include <rex/ppc/func.h>
#include <rex/ppc/context.h>
#include <rex/logging.h>
#include <unordered_set>
#include <stdexcept>
#include "performance.h"

REX_EXTERN(__imp__sub_822EADD8);
void ReportCleanupStack();

// Diagnose a corrupt linked list before the original recursive destructor
// exhausts the guest stack. Healthy lists use the unchanged guest routine.
REX_EXTERN(sub_822EADD8) {
  static thread_local bool processing=false;
  if(processing){__imp__sub_822EADD8(ctx,base);return;}
  std::unordered_set<uint32_t> seen;
  const auto next=[&](uint32_t node){const auto* p=base+node;return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];};
  for(auto node=ctx.r3.u32;node;node=next(node)) {
    if(!seen.insert(node).second) {
      REXLOG_CRITICAL("Cyclic guest cleanup list: root={:08X}, repeated={:08X}, nodes={}, caller LR={:08X}, SP={:08X}",ctx.r3.u32,node,seen.size(),uint32_t(ctx.lr),ctx.r1.u32);
      for(uint32_t offset=0;offset<64;offset+=4)
        REXLOG_CRITICAL("Cleanup node +{:02X}: {:08X}",offset,next(node+offset));
      ReportCleanupStack();
      WritePerformanceReport();
      throw std::runtime_error("Cyclic game cleanup list");
    }
    if(seen.size()>1000000)throw std::runtime_error("Unbounded game cleanup list");
  }
  struct Guard{Guard(){processing=true;}~Guard(){processing=false;}} guard;
  __imp__sub_822EADD8(ctx,base);
}
