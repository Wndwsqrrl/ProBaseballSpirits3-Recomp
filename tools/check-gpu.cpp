#include <Windows.h>
#include <dxgi1_6.h>
#include <d3d12.h>
#include <cstdio>
#include <cwchar>

int main() {
  IDXGIFactory1* factory=nullptr;
  if(FAILED(CreateDXGIFactory1(IID_PPV_ARGS(&factory))))return 1;
  int nvidia=-1;
  for(UINT index=0;;++index) {
    IDXGIAdapter1* adapter=nullptr;
    if(factory->EnumAdapters1(index,&adapter)!=S_OK)break;
    DXGI_ADAPTER_DESC1 desc{};
    adapter->GetDesc1(&desc);
    const bool supported=SUCCEEDED(D3D12CreateDevice(adapter,D3D_FEATURE_LEVEL_11_0,__uuidof(ID3D12Device),nullptr));
    std::wprintf(L"Adapter %u: %ls, vendor=%04X, dedicated VRAM=%llu MB, D3D12=%ls\n",index,desc.Description,desc.VendorId,
      static_cast<unsigned long long>(desc.DedicatedVideoMemory/(1024*1024)),supported?L"yes":L"no");
    if(desc.VendorId==0x10DE && supported && !(desc.Flags&DXGI_ADAPTER_FLAG_SOFTWARE))nvidia=int(index);
    adapter->Release();
  }
  factory->Release();
  if(nvidia<0)return 2;
  std::printf("NVIDIA_ADAPTER=%d\n",nvidia);
  return 0;
}
