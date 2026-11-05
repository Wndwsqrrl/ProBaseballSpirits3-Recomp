# Pro Baseball Spirits 3 Recomp

Native Windows port and English localization of the Japanese Xbox 360 release of **Pro Yakyuu Spirits 3**, built with [ReXGlue](https://github.com/rexglue/rexglue-sdk).

This repository contains port source, executable analysis metadata, English translation tables, and patch-building tools. Supply your own extracted game. Game files, generated game code, rebuilt archives, binaries, saves, and local analysis outputs are excluded.

## Status

- Boots on Windows with Direct3D 12 and prefers NVIDIA when available.
- Reaches the main menu, Exhibition setup, lineups, stadium introductions, and live pitching.
- English replaces native text through the game renderers, rather than a separate overlay.
- Current catalogue: **14,000 records / 13,735 unique fingerprints**. Counts include aliases and fragments; they are not a completion percentage.
- **47 texture labels** in six archive members cover menu modes, positions, lineup legends, handedness comparisons, home/away markers, and an input-screen Back label.
- Name lookups cover all **648 roster records**. Hanshin names are reviewed separately. Other families use the game's Latin jersey spellings; 325 additional given names use unambiguous readings from its name dictionary.
- Includes 308 newspaper lines/patterns and support for changing numbers and names in formatted messages.
- The latest offline wording pass improves 1,137 existing translations, including tutorials, player abilities, unlock requirements, statistics, and 119 newspaper lines/patterns. On-screen validation of this pass is pending.

Localization is unfinished. Some HUD elements, packed menu scripts, title graphics, stadium signage, and mode-specific text remain Japanese. Translation accuracy, remaining given names, and layouts still need review. Full-match stability and graphics performance are not established, and some gameplay geometry is missing. See [coverage status](translation/coverage-status.json) for recorded validation.

## Supported executable

| Field | Value |
| --- | --- |
| Platform / region | Xbox 360 / Japan |
| Title ID | `4B4E07D4` |
| Media ID | `07B4B9D2` |
| Version | `0.0.0.1` |
| default.xex SHA-256 | `903E2E94188DA3525C9CA39B9F8D9F27C3F6BEEE25B93A48C90921CDA3D8CDC0` |

The hooks, function registrations, and name-field patches target this executable. Setup checks its hash; translation and roster patches validate original bytes before writing.

## Build

Requirements: Windows x64, Visual Studio 2022 C++ build tools, LLVM/Clang, CMake, Ninja, Python 3, and an installed ReXGlue SDK/CLI compatible with 0.10.0. The tested CLI reports `0.10.0.0-dev.unknown`. Other SDK revisions and platforms are unverified.

```powershell
git clone https://github.com/Wndwsqrrl/ProBaseballSpirits3-Recomp.git
cd ProBaseballSpirits3-Recomp
$env:REXGLUE_SDK_INSTALL='C:/path/to/rexglue-sdk/out/install/win-amd64'
./tools/setup.ps1 -GameRoot 'C:/path/to/extracted-game' -RexGlue "$env:REXGLUE_SDK_INSTALL/bin/rexglue.exe"
./tools/build-port.cmd
```

Setup copies the extracted game into ignored `local/disc` and runs code generation with the checked-in manifest. If `local/disc` is prepared, pass that directory as `GameRoot`. The build wrapper uses the Visual Studio 2022 Community toolchain path; adjust it or configure the CMake preset from your developer shell for another installation.

The executable is written to `prospi3-recomp/out/build/win-amd64-release/prospi3.exe`.

## English assets and launch

Runtime text tables build from the checked-in English catalogue. To rebuild localized textures locally, install Pillow and run:

```powershell
python -m pip install Pillow
python tools/build-english-assets.py local/disc local/english-disc --labels translation/texture-labels.json --preview local/english-previews
./tools/play.ps1 -English
```

The asset builder reads the original disc and writes a separate English disc tree. It validates archive extents and rebuilt member hashes. Original game files remain unchanged. Latin glyph caches use installed Arial; no font file is distributed.

```powershell
./tools/play.ps1                                      # Original text and assets
./tools/play.ps1 -English -OriginalAssets              # English text, original assets
./tools/play.ps1 -AssetsOnly                          # English assets, original text
./tools/play.ps1 -English -TraceText                   # Capture unknown text locally
./tools/play.ps1 -English -Profile                     # Record submission timing
./tools/play.ps1 -English -Resolution 1080p -RenderScale 2 -Profile
```

`Resolution` sets the output window size. `RenderScale` requests an internal draw scale from 1 to 3; 2 means twice the native width and height. Higher settings are experimental and require visual and performance checks. `-NoVSync` is a separate experimental timing option; it does not establish a higher game frame rate. The currently installed runtime lacks FidelityFX support. Presentation effects require a compatible SDK build before they can be enabled.

The launcher selects Direct3D 12, adapter index 1 on the tested system, and the ROV render-target path. The port also enumerates NVIDIA adapters before graphics initialization. Verify the adapter name in startup logs on another machine.

## Translation tools

- `catalogue-text.py`: inspect executable display strings.
- `catalogue-runtime-text.py`: export unmatched renderer text from a local coverage audit.
- `draft-translation.py`: create cached translation drafts. Only extracted game text is submitted to Google Translate's public endpoint. Control tags and format arguments are protected; results require review.
- `curate-draft.py`: apply wording corrections and validate control-tag and printf-argument order.
- `apply-reviewed-ui.py`: merge the maintained `reviewed-ui.json`, `reviewed-abilities.json`, and `reviewed-headlines.json` corrections into the curation table before regenerating local drafts. Reviewed paragraphs may reflow line breaks; button prompts, color controls, and printf arguments remain protected.
- `generate-full-text.py`: generate the English render table and source-fingerprint catalogue. The full extracted Japanese corpus stays local; short runtime patterns are retained where required.
- `catalogue-name-readings.py`: decode the game's name dictionary. `catalogue-roster.py` combines name fields, Latin jersey spellings, reviewed Hanshin names, and unambiguous dictionary readings.
- `catalogue-menu-assets.py`: inventory textures and create local contact sheets.
- `build-english-assets.py`: replace atlas rectangles and rebuild a separate archive.

Scripts are under `tools/`. Unknown-text tracing writes `untranslated-text.tsv` and a short-glyph call-site trace under the selected user-data directory. Tracing and profiling are opt-in. Extracted text, caches, images, and traces stay under ignored `local/`.

Normal play keeps experimental pointer relocation disabled. English messages are translated at render boundaries; two bounded report formatters also translate completed pieces before appending and wrapping. Unsupported or ambiguous matches retain the original. Text sprite arrays grow at three verified allocation sites to accommodate longer English strings.

## Validation and performance

`tools/test-format-translation.cpp` checks format matching, malformed-input rejection, fullwidth numerals, name captures, and limits. `tools/audit-runtime-text.cpp` compares actual traces with the catalogue and loaded image. The coverage audit requires a locally generated translation header and a local loaded executable image.

The latest offline audit matched 463 captured strings; its only unmatched item was a square marker. This is a limited recorded trace, not full-game coverage. See [review validation](translation/review-validation.json) for the scope and deferred checks.

Frame profiles are buffered and flushed during a run so samples survive the runtime's hard-exit shutdown path. Summarize a matching gameplay interval with:

```powershell
python tools/summarize-performance.py local/userdata/performance-english-full.csv --start-seconds 60 --end-seconds 90
```

This measures submission cadence and text-hook CPU work, excluding guest rendering. It does not measure GPU completion. Compare the same scene, resolution, power mode, and shader-cache state. Menu timings and synthetic fixtures are not gameplay benchmarks.

## Runtime notes

- Leaf-function registrations and bounded switch tables are in `prospi3_functions.toml`.
- A project-local floating-point exception-mask override avoids the startup trap. The shared SDK is unchanged.
- Clipping guards and proportional Latin caches address zero-size glyph scaling and spacing issues.
- English match-entry corruption was traced to an undersized text sprite pool. The fix grows the original pool through the native allocator and checks exhaustion before unchecked index use.
- Routine audio warning spam is suppressed while decoding errors remain enabled. `PROSPI3_VERBOSE_AUDIO=1` restores warnings; the underlying XMA decoding issue is unresolved.

Keep original assets available for comparisons. Name-field changes can carry into saves created while the patch is active; keep backups when testing a season.

## Notices

This is an unofficial project, unaffiliated with Konami or the game's rights holders. Original game content is required locally and is not distributed here. ReXGlue-derived support code retains applicable notices in [licenses](licenses/).
