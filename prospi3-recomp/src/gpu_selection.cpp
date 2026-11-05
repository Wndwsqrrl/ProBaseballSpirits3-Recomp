#include <rex/cvar.h>
#include <rex/logging.h>
#include <stdexcept>
#include <string>
#ifdef _WIN32
#include <Windows.h>
#include <dxgi1_6.h>
#endif

void ConfigurePreferredGpu() {
#ifdef _WIN32
  IDXGIFactory1* factory=nullptr;
  if(FAILED(CreateDXGIFactory1(IID_PPV_ARGS(&factory))))
    throw std::runtime_error("Cannot enumerate DXGI graphics adapters");
  int selected=-1;
  for(UINT index=0;;++index) {
    IDXGIAdapter1* adapter=nullptr;
    if(factory->EnumAdapters1(index,&adapter)!=S_OK)break;
    DXGI_ADAPTER_DESC1 desc{};
    if(SUCCEEDED(adapter->GetDesc1(&desc)) && desc.VendorId==0x10DE &&
       !(desc.Flags&DXGI_ADAPTER_FLAG_SOFTWARE))selected=int(index);
    adapter->Release();
    if(selected>=0)break;
  }
  factory->Release();
  if(selected>=0) {
    if(!rex::cvar::SetFlagByName("gpu_backend","d3d12"))
      throw std::runtime_error("Cannot select D3D12 backend before graphics initialization");
    if(!rex::cvar::SetFlagByName("d3d12_adapter",std::to_string(selected)))
      throw std::runtime_error("Cannot select NVIDIA D3D12 adapter before graphics initialization");
    REXLOG_INFO("Selected NVIDIA DXGI adapter {} before graphics initialization",selected);
  } else {
    REXLOG_WARN("No NVIDIA adapter is available; retaining configured graphics adapter");
  }
#endif
}
