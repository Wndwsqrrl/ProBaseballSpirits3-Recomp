# Building from source

## Requirements

Windows x64, Visual Studio 2022 C++ tools, LLVM/Clang, CMake 3.25 or newer, Ninja, Python 3 and a compatible ReXGlue SDK/CLI. The tested SDK is the project's 0.10.0 development build; other SDK revisions are unverified.

Supply the supported Japanese Xbox 360 game described in the [project overview](../README.md). Game data and generated recompiled source are not included in the repository.

```powershell
git clone https://github.com/Wndwsqrrl/ProBaseballSpirits3-Recomp.git
cd ProBaseballSpirits3-Recomp
$env:REXGLUE_SDK_INSTALL='C:/path/to/rexglue-sdk/out/install/win-amd64'
./tools/setup.ps1 -GameRoot 'C:/path/to/extracted-game' -RexGlue "$env:REXGLUE_SDK_INSTALL/bin/rexglue.exe"
./tools/build-port.cmd
```

The game executable is written to `prospi3-recomp/out/build/win-amd64-release/prospi3.exe`.

## Build English assets locally

```powershell
python -m pip install Pillow
python tools/build-english-assets.py local/disc local/english-disc --labels translation/texture-labels.json --pennant-events translation/pennant-event-titles.json --pennant-text translation/pennant-event-text.json --packed-text translation/packed-text-slots.json --preview local/english-previews
```

The asset builder uses installed Arial Narrow Bold by default and requires Pillow with DDS encoding support. It creates a separate English tree and leaves the original archive unchanged. No font file is distributed.

## Development launch options

```powershell
./tools/play.ps1 -English
./tools/play.ps1
./tools/play.ps1 -English -OriginalAssets
./tools/play.ps1 -AssetsOnly
./tools/play.ps1 -English -TraceText
./tools/play.ps1 -English -Profile
```

The command-line development launcher retains its existing save-folder behavior. The release launcher uses separate language profiles.

Translation generation, source fingerprints, native replay checks and profiling are documented in the [technical notes](technical-notes.md). Maintained translation data lives in `translation/`; extracted game data, caches and binaries stay under ignored `local/` and build directories.
