// Offline XEX loading with the SDK; no guest entrypoint is executed.
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <rex/kernel/init.h>
#include <rex/logging.h>
#include <rex/runtime.h>
#include <rex/system/xex_module.h>
#include "english_patch.h"

int main(int argc, char** argv) {
  if (argc != 3) {
    std::cerr << "Usage: prospi3_inspect INPUT.xex NEW_OUTPUT_DIRECTORY\n";
    return 2;
  }
  try {
    namespace fs = std::filesystem;
    const auto input = fs::canonical(argv[1]);
    const auto output = fs::absolute(argv[2]);
    if (fs::exists(output)) throw std::runtime_error("Output already exists");
    const auto length = fs::file_size(input);
    if (length < 4 || length > 512ull * 1024 * 1024)
      throw std::runtime_error("Unsupported input size");
    std::vector<uint8_t> data(static_cast<size_t>(length));
    std::ifstream source(input, std::ios::binary);
    if (!source.read(reinterpret_cast<char*>(data.data()), data.size()))
      throw std::runtime_error("Cannot read complete XEX");
    rex::InitLoggingEarly();
    rex::LogConfig log;
    log.log_to_console = true;
    log.log_file = nullptr;
    rex::InitLogging(log);
    {
      rex::Runtime runtime(input.parent_path(), output, {}, output);
      if (runtime.Setup(rex::RuntimeConfig{
              .kernel_init = rex::kernel::InitializeKernel, .tool_mode = true}) != 0)
        throw std::runtime_error("Runtime setup failed");
      rex::runtime::XexModule module(runtime.function_dispatcher(), runtime.kernel_state());
      if (!module.Load(input.filename().string(), input.string(), data.data(), data.size()) ||
          !module.LoadContinue()) throw std::runtime_error("XEX loading failed");
      ApplyEnglishPatch(runtime);
      fs::create_directories(output);
      std::ofstream image(output / "loaded-image.bin", std::ios::binary);
      image.write(reinterpret_cast<const char*>(runtime.memory()->TranslateVirtual(module.base_address())),
                  module.image_size());
      if (!image) throw std::runtime_error("Image write failed");
      std::ofstream meta(output / "image.txt");
      meta << std::hex << "base=" << module.base_address()
           << "\nsize=" << module.image_size() << "\nentry=" << module.entry_point() << '\n';
      for (const auto& section : module.pe_sections())
        meta << section.name << " address=" << section.address << " size=" << section.size << '\n';
      if (!meta) throw std::runtime_error("Metadata write failed");
      std::cout << "base=0x" << std::hex << module.base_address()
                << " size=0x" << module.image_size() << '\n';
    }
    rex::ShutdownLogging();
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
