# Pro Baseball Spirits 3 Recomp

Native Windows port and English localization of the Japanese Xbox 360 release of **Pro Yakyuu Spirits 3**, built with [ReXGlue](https://github.com/rexglue/rexglue-sdk).

This repository contains port source, executable analysis metadata, English translation tables, and patch-building tools. Supply your own extracted game. Game files, generated game code, rebuilt archives, binaries, saves, and local analysis outputs are excluded.

## Status

- Boots on Windows with Direct3D 12 and prefers NVIDIA when available.
- Reaches the main menu, Exhibition setup, lineups, stadium introductions, and live pitching.
- English replaces native text through the game renderers, rather than a separate overlay.
- Current catalogue: **19,128 records / 18,829 unique fingerprints**. Counts include aliases and fragments. The catalogue excludes input codebooks.
- **2,098 texture label occurrences** across 263 atlases cover menu modes, umpire calls, pause menus, positions, editor and name-audio controls, practice captions, lineup legends, situational ability badges, handedness comparisons, utility and sound settings, opening opponent, venue and tournament captions, auto-game roles, pitcher order, result tables, pitching panels, calendar and newspaper status labels, DH lineup presets, batting-first controls, and country/custom-team labels.
- Twelve labels on results, editor, sound, shop, rotation and starter-order screens now fit their native sprite crops, including Home, Details, Number and Strikeouts. Decoded crop comparisons and all 2,223 archive members passed verification. The alternate mission/start-demo UV tiles were checked in a follow-up; live placement and animation remain pending. See [sprite crop validation](translation/static-sprite-crop-validation.json).
- All three Spirits opening titles fit their declared alternate crops. The six mission heading variants now use twelve separate prefix/suffix tiles, preserving their normal and bold masks. These six additional tile definitions do not add source headings. All 2,223 archive members passed verification. See [alternate sprite crop validation](translation/alternate-sprite-crop-validation.json); live assembly and animation checks remain pending.
- The DeepL comparison has responses for all 9,556 current distinct inputs. Source recovery covers all 25,407 current comparison records, including normalized custom roster glyphs and eleven previously missing AVG caption variants. Seventy-six formatting-sensitive sources have separate meaning-only examples. Ten initial context decisions and the 112-field training-table review retain verified baseball terminology; the broader manual accuracy review remains open. The comparison applies no automatic patch replacements. See [comparison status](translation/deepl-comparison-status.json).
- Lineup legends use Inact. for inactive roster status, Power for pitching power, and separate Basic Stamina / Starter Stamina labels. Team selection says Bat First / Bat Last. All 2,098 localized texture occurrences have transcribed source text for comparison; 57 missing sources were checked against decoded originals. Six wording corrections and the full archive passed verification; live placement remains pending. See [texture wording validation](translation/texture-source-wording-validation.json).
- All 13 stadium-selection cards have English venue names and surface/dimension headings in their day and night views. Checks preserve the stadium model regions and original dimensions. In-game placement is pending.
- Four regional/USA stadium photo captions have English day/night labels, including the original provisional qualifier. Caption cleanup uses the companion photos and local pixels where the old lettering overlaps. Japanese ads remain in the photos, with all pixels outside the caption rectangles unchanged. See [photo caption validation](translation/stadium-photo-caption-validation.json). Live placement remains pending.
- Given-name patches cover all **648 roster records**, including two names stored with custom game characters. Historical records verify 549 non-Hanshin given names. Another 45 use the game's name dictionary, and the Hanshin readings are documented separately.
- Includes 310 newspaper lines/patterns and support for changing numbers and names in formatted messages.
- The patch includes **77 reviewed menu and matchup entries**, including team records and mode descriptions.
- The name pool includes **418 reviewed name fields**. The review uses native Latin surnames, the game's Japanese name dictionary, the original roster, and the original display spellings. Provisional given-name choices remain drafts where an individual reading or preferred spelling cannot be confirmed.
- The announcer-name selector has **1,256 English labels**, with 144 spelling overrides and phonetic transliteration for the remaining kana names. Its navigation grid displays 46 English syllables, fitted within the native cells. In-game placement still needs checking.
- Pitching-style and settings labels use the 2026 terms **Submarine**, **Medium Speed**, and **CPU Difficulty**, including their compound labels and generation maps. Twenty entries, 28 compiled lookups and the Windows build were checked; live placement remains pending. See [motion and settings validation](translation/motion-settings-wording-validation.json).
- The executable-backed catalogue has **5,907 reviewed entries and 390 drafts**. It includes Xbox Live dialogs, pitch names, team and venue labels, standings, and milestone text.
- All 56 Spirits training names and 56 descriptions have exact renderer lookups (108 unique sources) and a completed source/DeepL accuracy review. The reviewed wording retains level/XP differences, durations and partner restrictions. The 112 maintained review overrides and 108 compiled lookups passed; the generated text header is byte-identical. Native records are unchanged. Their display route and live layout remain unverified. See [training accuracy review](translation/spirits-training-accuracy-validation.json). See [training lookup validation](translation/spirits-training-integration-validation.json).
- The 39 integrated UI fields have a source/DeepL context review. Thirty-seven CP932 entries are reviewed; two historical draft/free-agency descriptions now specify the actual 2005 assignments. Seventy-four source/filled cases, 37 maintained mappings, 45 native offseason message replays and the Windows build passed. The test-PC prompt keeps its specific purpose; the shared year pattern remains a draft pending duration-context coverage. Live placement remains open. See [native UI accuracy review](translation/native-ui-accuracy-validation.json).
- Contract amounts with the full ten-thousand-yen suffix now use the existing `x 10,000 yen` format, including fullwidth input numbers. Thirteen compiled cases and the Windows build passed. Native amount buffers remain unchanged; live amount-column placement is pending. See [contract currency validation](translation/contract-currency-validation.json).
- All 207 settings explanations and 48 option labels have a source/context review. Fourteen paragraphs clarify automatic tactics, the two assisted pitch markers, Pitch Power, Medium speed and CPU difficulty. The follow-up reviews 261 fragment sources, corrects 79 mappings and maintains 258 explicit renderer runs. Three incomplete word endings no longer receive unrelated English lines. All native fields and full settings paragraphs are unchanged; 465 lookups, 258 regeneration/curation checks, policy regressions and the Windows build passed. Live layout remains open. See [settings accuracy review](translation/settings-accuracy-validation.json). See [fragment review](translation/settings-fragment-accuracy-validation.json).
- Pitcher attributes distinguish Starter Conditioning (Starter Cond. in compact labels) from the Starter Prep instruction. Fatigue Recovery uses its full name in explanations and Recovery where compact. Nine runtime rows and one Pennant reward passed 15 compiled cases, the Windows build and full archive verification. Live stat/bonus fit remains pending. See [conditioning validation](translation/starter-conditioning-validation.json).
- Mission and camp help consistently use Coach Capacity and Boost missions, with explicit active-roster eligibility. The 34-page source/DeepL review corrected seven catalogue rows; 40 compiled cases, 35 maintained mappings and the Windows build passed. Starter-stat naming was aligned in a follow-up; live placement remains open. See [mission help accuracy review](translation/mission-help-accuracy-validation.json).
- Pennant date and nominee strings now format as `4/2`, `As of 4/2`, and `- 1 more -`. Additional wording updates cover Tigers cheers, award-stat units, the pitching heading, and the Fullcast venue identifier.
- Pitching columns **H vs L** and **H vs R** count hits allowed against left- and right-handed batters. **Fielder Use** is the average number of fielders used per game. These meanings were checked against native calculations and the 2026 terminology. See [native stat validation](translation/native-stat-definition-validation.json).
- The team pitcher-use editor uses **1st–7th** across the starter, reliever and closer columns. **Pitcher Use** means pitchers used per game, matching the native calculation and the 2026 term. Six native cases, eight compiled lookups and the Windows build passed; live placement remains unchecked. See [pitcher usage validation](translation/pitcher-usage-wording-validation.json).
- Player-data ability previews use **CON R**, **CON L**, and **Power**. The native grade paths confirm their meaning. All nine labels in that atlas fit the original sprite crops, with the existing K, km/h and BP graphics preserved. See [player-data label validation](translation/player-data-label-validation.json).
- **39 match captions** have English templates for live streaks, milestones, and batting averages. The templates passed offline tests with values assembled in the native format. Fifty-five fallback fragments now use baseball wording; two templates use the 2026 meaning of 3+ hit games. The update passed 271 compiled lookups. The updated Windows build passes; live placement checks remain. See [caption wording validation](translation/match-fallback-wording-validation.json).
- **213 pitching delivery and batting stance labels** matched their intended English in offline checks.
- **118 career dialogue lines** cover coaching feedback, pregame instructions, and roster notices. Career rows reach the proportional Latin font as complete lines.
- Match recaps include **51 complete manager comments** assembled from the game's phrase table. Forty-three fallback phrases have revised baseball wording and remain drafts pending live context checks. See [manager fallback validation](translation/manager-fallback-wording-validation.json). The outer verdict has 15 reports checked across 30 seeded native cases. Offense/Defense headings and the report prefix have clearer formatting; eleven additional fallbacks have revised wording. A larger [pipeline check](translation/manager-report-pipeline-validation.json) exercises native generation, sorting and selection on 15,522 seeded inputs. All 73 nonempty pieces matched English lookups and fit the tested byte limits. Real-match statistics, rating derivation and live wrapping remain unchecked. See [outer verdict validation](translation/manager-verdict-wording-validation.json).
- Legacy newspaper snippets use baseball wording for a scoreless inning and a go-ahead run. Four 2005 draft-option snippets distinguish grouped rookie entry from historical club assignment. Incomplete newspaper sources remain drafts. See [wrapped text validation](translation/legacy-wrapped-wording-validation.json).
- All 12 club previews have reviewed English. The latest preview and pregame help lines pass offline width and line-budget checks. In-game placement is pending.
- **83 packed text slots** in 15 archive members cover the scoreboard, calendar, stats, trade, contract, and trial screens. Each edit fits the original slot. The verifier confirmed 2,112 unmodified archive members match the original bytes.
- **374 packed menu lookups** include 177 menu defaults checked against their original rectangles. Five character grids in the parsed menu text are kept for native name input.
- The English build sets the Xbox storage display title to `Pro Yakyuu Spirits 3` when the game prepares its save metadata. The save key stays `Save Data`.
- Eighteen formatting-sensitive Pennant event fields have a source/DeepL meaning review. Six bounded wording edits clarify recovery, pacing, partial resolution, bullpen handoffs and career milestones. Player/team/count controls are preserved; all event fields and archive members passed verification. Native placeholder expansion and live placement remain pending. See [event meaning review](translation/pennant-event-meaning-validation.json).
- The asset patch includes all **940 populated fields** across **187 Pennant events** in `PEMDFIX.CHK`, including titles, goals, rewards, and stories. Event screens still need an in-game layout check.

Pitching-practice instructions cover both Y/A button variants. Fielding-practice “Hit Again” and “Re-Do Last Practice” use the official 2026 wording, fitted across the original joined sprite strips. Offline checks preserve the controls and earlier English labels; live checks remain. See [practice help validation](translation/practice-help-validation.json).

Magazine edition badges, the newspaper masthead, the baseball tag, and the postal classification have English text. The original title prompt is already English. The blurred edition marks, background columns, and pinned notice print remain unresolved. See [print heading validation](translation/print-heading-validation.json).

Generated-player name coverage includes **4,956 complete-name lookups for all 413 native name pairs**, covering combined, spaced and mixed Latin/Japanese forms. Of those pairs, **163 are reviewed and 250 have provisional readings**. Each lookup retains both name fields. Chinese-group names use native Latin surnames and provisional kana-based given-name transcriptions; these do not establish preferred Chinese spellings. Korean given-name readings and some fictional Japanese readings also remain provisional. Surnames use the native Latin registration where a shared source needs a record-specific spelling. The given name Masaru uses record-specific mappings so the win-statistic label remains W. Surname-only widgets and live placement remain unchecked. This is full-name lookup coverage, not a whole-game completion claim. See [complete name-pool validation](translation/complete-name-pool-validation.json), [Chinese name context validation](translation/chinese-name-context-validation.json), and [remaining Japanese name context validation](translation/remaining-japanese-name-context-validation.json).

The latest caption and manager wording passed both a staged compile/link check and the normal Windows build. Live validation of the updated executable remains pending. See [build validation](translation/manager-build-validation.json).

Localization remains unfinished. Credits may remain Japanese. The main title logo retains its original Japanese lettering, glow and shadow. The original in-stadium signs, sponsor ads and ballpark artwork are preserved; earlier English credit title and licensing captions are retained.

The partial interface review documents [4 textures awaiting localization or native-context review](translation/interface-texture-review.json). The [extended review](translation/extended-interface-texture-review.json) has no untranslated candidates left in its current inventory; live placement checks remain. The remaining blurred [slot-reel strip](translation/slot-concealment-validation.json) is a native concealment effect and retains its original pixels; 500 native selector cases match an independent replay of the generated function. Its live transition remains unchecked. These are partial inventories, not a full-game coverage denominator.

The earlier nonstandard-name candidate queue is now classified; the final pass inspected 218 records and preserved all 169 source members byte-identically. See [remaining family review](translation/remaining-family-review.json). Translation accuracy, ambiguous name aliases, live layouts, unvisited branches and the final comparison review remain. Full-match stability and graphics performance are not established, and some gameplay geometry is missing. See [coverage status](translation/coverage-status.json).

The localization goal is English for the playable interface, including menus, prompts, instructions, reports, and gameplay HUD text. Japanese presentation such as the title logo, team logos, stadium signs, sponsor ads, and ballpark artwork is part of the original NPB atmosphere and can stay as it is.

The [file-based gap audit](translation/coverage-discovery.md) lists interface strings missing from the current build, entries with draft English, and paths that still need discovery.

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

Runtime text tables build from the checked-in English catalogue. To rebuild localized textures locally, install Pillow with DDS encoding support for DXT1, DXT3, and DXT5, then run:

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
- `apply-reviewed-ui.py`: merge the maintained `reviewed-ui.json`, `reviewed-abilities.json`, `reviewed-headlines.json`, `reviewed-settings.json`, `reviewed-settings-fragments.json`, `reviewed-modes.json`, and `reviewed-management.json` corrections into the curation table before regenerating local drafts. Reviewed paragraphs may reflow line breaks; button prompts, color controls, and printf arguments remain protected.
- `generate-name-pool-lookups.py` builds complete-name lookups from the supported loaded image, reviewed fields, contextual overrides and the original 413-record name table. It retains unresolved names for further review.
- `generate-full-text.py` builds the English render table and source-fingerprint catalogue. It retains short runtime patterns where required. The default `translation/fragment-policy.json` prevents positional fragment inference for the reviewed settings sources and rejects the listed incomplete endings from address-zero lookups. Explicit native fields remain eligible. When regenerating from local draft inputs, include `--extra-catalogue translation/reviewed-settings-fragments.json` for reviewed settings runs, `--extra-catalogue translation/reviewed-asset-text.json` for packed UI lookups, `--extra-catalogue translation/manager-report-lookups.json` for manager comments, the output of `generate-match-captions.py` for live stat captions, and `--extra-catalogue translation/generated-name-lookups.json` for complete generated-player names.
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
