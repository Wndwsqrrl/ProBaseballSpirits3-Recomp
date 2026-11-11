# Pro Baseball Spirits 3 Recomp

Native Windows port and English localization of the Japanese Xbox 360 release of **Pro Yakyuu Spirits 3**, built with [ReXGlue](https://github.com/rexglue/rexglue-sdk).

This repository contains port source, executable analysis metadata, English translation tables, and patch-building tools. Supply your own extracted game. Game files, generated game code, rebuilt archives, binaries, saves, and local analysis outputs are excluded.

## Status

- Boots on Windows with Direct3D 12 and prefers NVIDIA when available.
- Reaches the main menu, Exhibition setup, lineups, stadium introductions, and live pitching.
- English replaces native text through the game renderers, rather than a separate overlay.
- Current catalogue: **14,020 records / 13,726 unique fingerprints**. Counts include aliases and fragments. The catalogue excludes input codebooks.
- **161 texture labels** across 27 atlases cover menu modes, umpire calls, pause menus, positions, lineup legends, handedness comparisons, utility and sound settings, auto-game roles, pitcher order, result headings, DH lineup presets, batting-first controls, and country/custom-team labels.
- Given-name patches cover all **648 roster records**, including two names stored with custom game characters. Historical records verify 549 non-Hanshin given names. Another 45 use the game's name dictionary, and the Hanshin readings are documented separately.
- Includes 308 newspaper lines/patterns and support for changing numbers and names in formatted messages.
- The patch includes **77 reviewed menu and matchup entries**, including team records and mode descriptions.
- The name pool includes **376 reviewed names**. The review uses native Latin surnames, the game's Japanese name dictionary, and the original display spellings.
- The announcer-name selector has **1,256 English labels**, with 144 spelling overrides and phonetic transliteration for the remaining kana names. Its navigation grid displays 46 English syllables, fitted within the native cells. In-game placement still needs checking.
- The main extracted list has **5,724 reviewed entries and 464 drafts**. It includes reviewed Xbox Live dialogs, pitch names, team and venue labels, standings, and milestone text.
- **39 match captions** have English templates for live streaks, milestones, and batting averages. The templates passed offline tests with values assembled in the native format.
- **213 pitching delivery and batting stance labels** matched their intended English in offline checks.
- **118 career dialogue lines** cover coaching feedback, pregame instructions, and roster notices. Career rows reach the proportional Latin font as complete lines.
- Match recaps include **51 complete manager comments** assembled from the game's phrase table.
- All 12 club previews have reviewed English. The latest preview and pregame help lines pass offline width and line-budget checks. In-game placement is pending.
- **83 packed text slots** in 15 archive members cover the scoreboard, calendar, stats, trade, contract, and trial screens. Each edit fits the original slot. The verifier confirmed 2,191 unmodified archive members match the original bytes.
- **374 packed menu lookups** include 177 menu defaults checked against their original rectangles. Five character grids in the parsed menu text are kept for native name input.
- The English build sets the Xbox storage display title to `Pro Yakyuu Spirits 3` when the game prepares its save metadata. The save key stays `Save Data`.
- The asset patch includes all **940 populated fields** across **187 Pennant events** in `PEMDFIX.CHK`, including titles, goals, rewards, and stories. Event screens still need an in-game layout check.

Localization is unfinished. Some HUD elements, packed menu scripts, title graphics, and mode-specific text remain Japanese. An additional review decoded 326 interface textures and documented 69 textures that still contain Japanese; see [interface texture review](translation/interface-texture-review.json). Translation accuracy, ambiguous name aliases, and layouts still need review. Full-match stability and graphics performance are not established, and some gameplay geometry is missing. See [coverage status](translation/coverage-status.json) for recorded validation.

The English patch covers the game interface. In-stadium signage, sponsor ads, and other ballpark artwork retain their original Japanese presentation.

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
python tools/build-english-assets.py local/disc local/english-disc --labels translation/texture-labels.json --pennant-events translation/pennant-event-titles.json --pennant-text translation/pennant-event-text.json --packed-text translation/packed-text-slots.json --preview local/english-previews
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
- `apply-reviewed-ui.py`: merge the maintained `reviewed-ui.json`, `reviewed-abilities.json`, `reviewed-headlines.json`, `reviewed-settings.json`, `reviewed-modes.json`, and `reviewed-management.json` corrections into the curation table before regenerating local drafts. Reviewed paragraphs may reflow line breaks; button prompts, color controls, and printf arguments remain protected.
- `generate-full-text.py` builds the English render table and source-fingerprint catalogue. It retains short runtime patterns where required. When regenerating from local draft inputs, include `--extra-catalogue translation/reviewed-asset-text.json` for packed UI lookups, `--extra-catalogue translation/manager-report-lookups.json` for manager comments, and the output of `generate-match-captions.py` for live stat captions.
- `generate-match-captions.py IMAGE translation/match-captions.json OUTPUT` reconstructs native stat-caption patterns from the supported loaded image and the English caption list.
- `generate-headline-patterns.py`: create bounded name/number aliases for filled newspaper headlines, preserving the original field order.
- `check-text-layout.py`: check reviewed settings text against an approximate Arial width and line budget. Requires Pillow; this is an offline estimate, not a measurement of game rectangles.
- `catalogue-name-readings.py`: decode the game's name dictionary. `catalogue-roster.py` combines name fields, Latin jersey spellings, reviewed roster names, and unambiguous dictionary readings. Pass `--reviewed-roster` for each reviewed name file.
- `generate-announced-names.py EDIT.CHK translation/announced-name-spellings.json prospi3-recomp/src/announced_names.h` regenerates announcer-name labels from the decoded editor resource.
- `catalogue-menu-assets.py`: inventory textures and create local contact sheets.
- `pennant_events.py`: export the ten fields of each event from an extracted, decoded `PEMDFIX.CHK`.
- `build-english-assets.py`: replace atlas rectangles, packed menu text, and Pennant event text in a separate archive.

The Japanese 2006 release defines the meaning of each string. KONAMI's English [PRO SPIRIT 2026 game FAQ](https://www.konami.com/games/2026_support/faq/0/us/en-us/pc/category?category=1) helps cross-check shared terminology such as Manager Mode, Hit-and-Run, and Off. Pro Spirits 3 describes its ウエスト sign as a response to an attempted steal, so the patch calls it Pitchout.

Scripts are under `tools/`. Unknown-text tracing writes `untranslated-text.tsv` and a short-glyph call-site trace under the selected user-data directory. Tracing and profiling are opt-in. Extracted text, caches, images, and traces stay under ignored `local/`.

Normal play keeps experimental pointer relocation disabled. English messages are translated at render boundaries; two bounded report formatters also translate completed pieces before appending and wrapping. Unsupported or ambiguous matches retain the original. Composed player assessments also use a phrase matcher restricted to the original report table and five known period/topic prefixes. It requires a complete, unambiguous match and stores the result in the existing output cache. Text sprite arrays grow at three verified allocation sites to accommodate longer English strings.

## Validation and performance

`tools/test-format-translation.cpp` checks format matching, malformed-input rejection, fullwidth numerals, padded name captures, and limits. Formatted messages support up to eight ordered fields while retaining the input, output, and matching-work limits. Multiline fitting measures the widest line rather than only the heading; left, center, and right alignment remain native. `tools/audit-runtime-text.cpp` compares actual traces with the catalogue and loaded image. The coverage audit requires a locally generated translation header and a local loaded executable image. `tools/test-report-translation.cpp` verifies supported-image fingerprints and constructs pitcher, batter, and coach assessments from native table phrases. These fixtures check composition, punctuation, unknown-text rejection, and work limits; they do not establish live report rendering.

The recorded-trace audit matched 463 captured strings; its only unmatched item was a square marker. This is a limited recorded trace, not full-game coverage. See [review validation](translation/review-validation.json) for the scope and deferred checks. The 74 fixed-row manager descriptions also pass a source-derived offline width estimate; see [management layout validation](translation/management-layout-validation.json).

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
