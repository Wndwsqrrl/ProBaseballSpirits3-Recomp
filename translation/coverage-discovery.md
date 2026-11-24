# English localization gap audit

The goal is English for the playable interface. Title and team logos, stadium signage, sponsor art, and other presentation artwork can retain their Japanese text. This audit uses the supported Xbox 360 image, decoded game files, the current local English catalogue, and existing renderer traces. The results describe what can be established from those files.

## Native text found by the audit

The scans initially found **36 native UI sources without complete English coverage**. These included 13 ordinary CP932 strings, 21 offseason messages with embedded controls, one UTF-16BE system prompt, and one year format. [All 36 have draft English](native-ui-drafts.json) integrated into the local Windows build. The draft file uses CP932 by default and explicitly marks the UTF-16BE entry.

Every readable, in-scope source itemized in this audit now has an English draft or an existing translation. The draft files cover **165 native fields**, including duplicates. The local build includes 39 native UI fields and exact renderer lookups for all 112 Spirits training fields, covering 151 of the 165 itemized fields. Training display routing and live placement remain unverified. The remaining **14 unintegrated English drafts** comprise 13 save-section metadata labels with no display consumer identified and one hidden startup placeholder. Additional text can still surface in unvisited game paths. [Final draft validation](final-draft-validation.json)

| Area | Missing content | Native address |
| --- | --- | --- |
| Controller recovery | Reconnect the controller and press A to continue | `0x82068400` |
| Challenge | Get one out | `0x82076280` |
| Player display | Player Name | `0x820638E8` |
| Player stats | Contact vs RHP | `0x82065020` |
| Team arrangement | Arrange Menu | `0x8207E320` |
| Team filter | All Teams | `0x82091070` |
| Player editor | Original Player 1 | `0x820A2810` |
| Xbox Live | Match Conditions | `0x820852FC` |
| Xbox Live | Search Filters | `0x820857AC` |
| Xbox Live | Select Search Type | `0x82085EB4` |
| Xbox Live | Team Rankings and the notice that the statistics service has ended | `0x82085EF8` |
| Xbox Live | Xbox Live Mode | `0x820860E8` |
| Xbox Live | Ranked Match | `0x820864D8` |
| System keyboard | Enter the IP address of the check PC | `0x82086190` |
| Year display | Numeric year followed by the Japanese year marker | `0x82091A28` |

`Contact vs RHP` has an English curation rule, but the compiled catalogue has no lookup for the native bytes at this address. The controller prompt has a translated tail at `0x82068414`, while the native controller handler passes the full prompt at `0x82068400`.

The IP prompt is the UTF-16BE description passed to `XamShowKeyboardUI` at `0x8246D620`, outside the CP932 text renderer. Its title is `INPUTADDR`. The files establish the dialog call. They do not establish how this branch is reached through the current Windows UI.

The year format `%d年` reaches six native formatting calls across `0x824D3728`, `0x824D4B38`, and `0x824D5738`. The callers format the year and copy the result into a text field. The compiled lookup failed for 2005, 2006, 2007, and 2010 with both ASCII and fullwidth digits. The English draft keeps the number alone.

The Game Settings (`0x8207F210`), Ranked Match Lobby (`0x82085C60`), and Preseason Results (`0x8209F10C`) headers now have full-string lookups in the build. Their drafts preserve button tags. The placeholder header and save-section labels remain staged. The as-of-date suffix at `0x82091440` is already covered when assembled with the month and day. [Context-dependent drafts](native-ui-context-drafts.json)

### Offseason messages

These 21 source strings contain an embedded `0x0B` formatting byte that the native formatter handles separately from a newline. The ordinary extractor skipped these sources. None matched a full English lookup with or without that byte. Nine have English for at least one Japanese fragment when split at the formatting and newline boundaries. Earlier translations for the two 2005 draft options also cover separate text fragments. The full passages remain open. The formatter at `0x824F4630` is referenced by the draft and free-agent paths and separates the control bytes while preparing display text. Several callers insert live team names, player names, and counts before sending text to that formatter.

| Area | Missing complete message | Native address |
| --- | --- | --- |
| Draft | A team passes, the number of rounds left, and an instruction to advance | `0x820946F8` |
| Roster help | Review your current roster and highlight a player to see abilities | `0x82094770` |
| Draft | A team has drafted a named player, with rounds left | `0x82094820` |
| Draft | Wait for a named team to make its waiver-order pick | `0x82094868` |
| Draft | Choose your waiver-order pick, with rounds left | `0x820948D0` |
| Draft | Wait for another team to make its free-acquisition-slot pick | `0x82094918` |
| Draft | Pick a player using a free-acquisition slot | `0x8209495C` |
| Draft | Choose fictional players to enter | `0x820949E0` |
| Draft | Recreate the historical 2005 picks and club assignments | `0x82094A38` |
| Draft | Enter the real 2005 rookies as a group | `0x82094AC0` |
| Draft | Choose custom players from Spirits Mode to enter | `0x82094B38` |
| Free agency | A team passes, the number of selections left, and an instruction to advance | `0x820954BC` |
| Free agency | A team has signed a named player, with selections left | `0x82095560` |
| Free agency | Wait for a named team to select a player | `0x820955A0` |
| Free agency | Choose a player to sign, with selections left | `0x820955E8` |
| Free agency | Wait for another team to choose a signing | `0x82095618` |
| Free agency | Recreate the historical 2005 signings and club assignments | `0x82095678` |
| Free agency | Enter the real players eligible in 2005 as a group | `0x82095720` |
| Free agency | Choose custom players from Spirits Mode to enter | `0x820957B0` |
| Roster help | Alternate explanation of the roster and player ability preview | `0x82096968` |
| Player selection | Wait while another team selects a player | `0x820969CC` |

## Staged drafts and remaining display context

| Candidate | Evidence and remaining question |
| --- | --- |
| Spirits training names and descriptions | The indexed table at `0x827D8908` contains 56 records at a `0xF8`-byte stride. Each has a CP932 name at `+0x0C` and a description at `+0x20`. The native Spirits card code in `0x825AFB90` selects and copies records to a card object. Its virtual accessor at `0x821E15B8` returns that copied record. The display path from that accessor remains unverified. Exact lookups for all 112 fields are now compiled without modifying the native records. Existing English training-card artwork has separate coverage. |
| Special-selection limit warning | Identical Japanese at `0x827DBD78` and `0x827DBE70` is the description in the last two Spirits training records. The meaning is “Too many Special selections.” Both copies are included in the table count. |
| Dummy Title | The startup routine assigns the header at `0x823A04E4` and hides the same object at `0x823A04F0` before advancing its state. The English reference draft preserves all four control tags. |
| Save-section labels | The table at `0x8273E098` pairs the 13 UTF-16BE labels with ASCII section keys. The traced save-data processing uses size and offset fields, and the separate storage display title at `0x820A6F94` already has an English patch. The 13 labels have no confirmed display consumer. Ten English drafts exceed the available space before their adjacent section key. |
| Printed newspaper and career-board artwork | `PNTODAY06.CHK / MENU_PEtoday_base.tsr` retains blurred edition marks and background columns. `SOLOINFO.CHK / MENU_PEtuti_00.tsr` and `_02.tsr` retain blurred pinned-paper microprint. The main headings and markers have English. Enlarged source crops do not establish readable instructions in the background art. |

The scorecard atlas `RESSB.CHK / MENU_YAM_score_99_02.tsr` consists of team marks and falls under the logo preservation scope. The blurred Spirits slot strip is a verified native concealment effect. The pitch-name character grid remains available for native text entry.

Before the training integration, **53 of 56 names lacked a compiled whole-field lookup even after the space-removal fallback**; two matched after removing inserted spaces and one normalized to Latin letters. All **56 descriptions lacked complete compiled English**. Seven matched one line apiece and the other 49 had no matching line in that earlier probe. All 112 fields now have exact renderer lookups, verified through 108 unique compiled probes and 112 curation checks. All earlier catalogue rows remain unchanged. The native records are not overwritten; their nonzero description tails remain intact. The prior 351 px width estimate in Arial at 16 px is an offline estimate. Display routing and actual screen fit remain unverified. [Training lookup integration](spirits-training-integration-validation.json) · [Spirits training drafts](spirits-training-drafts.json) · [Final draft validation](final-draft-validation.json)

## Draft English already present

| Area | Remaining review |
| --- | --- |
| Executable-backed text | 427 drafts across the current 6,297 address-backed entries. The older 389 include 258 name-related entries, 57 match-caption fragments, 54 manager-report fragments, and 20 short strings such as counters and units. The native UI integration added 38 CP932 drafts. The 112 training fields have since passed a source/DeepL wording review and are reviewed entries, with display routing still unverified. |
| Generated player names | 250 of 413 full names have provisional readings. Their English is already present. Surname-only widgets and preferred given-name spellings still need review. |
| Dynamic newspaper and season copy | Existing traces include six already-drafted recap fragments. The source splits a hitter’s name across two chunks and truncates part of an article around a 6–7 score. Review the complete article and its wrapping together. The packed month label for October is also still marked draft. |

## What the scan covered

- The executable scan checked 6,353 CP932 candidates. It found 14 misses in the first pass. Inspection accounted for these as included-string tails, binary or glyph tables, or a start address already corrected in curation. A second pass followed PowerPC address constructions and found 57 additional printable candidates. Of their 52 lookup misses, 18 are itemized above as UI sources, fragments, or context candidates. The other 34 resolve to interior bytes or binary data under this scan. A sweep of aligned alternate starts exposed the formatting byte. Rescanning the address constructions for strings containing it found the 21 offseason messages.
- The `TXCPACK` parser found 1,434 nonblank records across 325 chunks, with zero parse errors. Among the 1,050 records containing Japanese, 961 have reviewed compiled lookups, 83 are patched directly, one has draft English, and five are rows of the pitch-name input grid. The lookup results are file-level checks.
- A prose scan checked 8,270 additional chunk payloads after skipping recognized texture, model, motion, font, and packed resource types. Its 102 matches were in the known announcer-name and Pennant event tables. A separate check matched all 308 populated slots in the executable’s fixed 309-slot headline table to reviewed catalogue entries.
- Texture metadata covered 13,124 occurrences across the main archive and loose resources. All 450 `MENU`/`GAME`-prefixed occurrences and all 704 textures in patched atlas members were present in a prior inventory or the current patch. The remaining archive families are predominantly face, uniform, lighting, scene, mascot, and vehicle assets. This establishes metadata coverage for those families. Only selected previews were visually inspected in this audit.
- The two nonempty historical traces contained 464 distinct inputs. The current compiled audit matched 463, including 16 with draft English. The sole unmatched input was the square glyph `■`.
- The generated C++ pass propagated constant pointers through register setup, branches, and loads in 1,088 functions containing calls to known text routines. It inspected 2,639 unique call locations or tail-call blocks and recovered 342 Japanese text-and-call-route pairs for comparison against the current catalogue. These are candidate and call-route counts. Runtime-only pointer values, indirect calls, and unbounded composition can fall outside this pass.
- The loaded image's existing `.data` inventory contributed 8,128 raw string candidates. Single-glyph maps, binary coincidences, roster fields, and stadium-banner strings account for many raw lookup misses. The Spirits training table was separated from these by its fixed record stride and native references. A separate CP932 prose scan of 293 `SBIB` layout chunks and 2,520 `GSNB` script chunks found no additional candidates under its printable-text filter.

The largest remaining discovery gaps are generated text in unvisited Pennant and career branches, rare gameplay events and reports, and the context of platform dialogs and short HUD fragments. Those can produce variants from changing numbers, names, or game state. This file audit establishes an actionable backlog. Exhaustive screen coverage and formatting still require checking representative rendered cases for those paths.

The headless validation replayed the generated offseason splitter with names, counts, and literal percent characters. It verified exact row output for 45 messages, tested both plain and fullwidth year digits, and estimated menu and Spirits training widths. [Headless formatting validation](headless-formatting-validation.json)

## Native sprite crop follow-up

A static crop scan covered all 263 localized atlases, with SBIB draw references found for 190. Of 88 geometric candidates, 16 lost rendered ink at an individual draw crop. Twelve labels were refitted to their native rectangles and verified in decoded crop comparisons. The two Complete strips meet on screen and remain unchanged. The three remaining default crop cases were followed through the declared TXCPACK UV tables: all nine heading variants now fit their alternate tiles, while live animation and assembled placement remain unchecked. Labels on atlases without static bindings also retain their separate placement/discovery requirements. The rebuilt English archive passed checks for all 2,223 members, including 2,112 untouched members. [Static sprite crop validation](static-sprite-crop-validation.json)

The alternate UV follow-up verified three Spirits title rectangles and twelve mission prefix/suffix rectangles directly from the original layout packs. The mission records now define twelve tiles instead of six compound labels, raising the total to 2,098 label occurrences without adding source headings. All 2,223 archive members passed again. The static ink scan now leaves only the intentionally joined Complete strips; this does not clear unbound atlases or prove every animated frame. [Alternate sprite crop validation](alternate-sprite-crop-validation.json)

The contract-renewal review found a numeric composition gap beyond individual source fields: the short 万 amount pattern existed, but the full 万円 suffix assembled by the native contract and salary-summary code did not match. The full numeric pattern is now integrated and passed 13 compiled cases. This illustrates why dictionary coverage does not prove coverage of dynamically composed text. Live salary-column placement remains pending. [Contract currency validation](contract-currency-validation.json)

The original-image comparison transcribed the final 57 localized texture sources that lacked metadata, so all 2,098 current label occurrences now have source text. This exposed an incorrect Tired legend for 抹消: the corrected Inact. label denotes inactive roster status. Power, Basic Stamina and Starter Stamina follow the 2026 terminology in the compact pitcher panel. Bat First / Bat Last describes the original selection labels more directly than Away / Home. Six corrected labels across two atlases passed decoded visual and full-archive checks; live layout remains pending. [Texture source and wording validation](texture-source-wording-validation.json)

The DeepL service pass returned all 9,559 distinct known inputs. Source reconstruction now covers every one of the 25,410 comparison records: eleven static 1.000 AVG captions were regenerated from the checked native caption table, and the two custom roster glyphs were normalized for comparison using the already verified NPB player records. Fifty-four XML-control differences and 22 additional Pennant-control differences have separate plain-text examples with sample arguments. They are comparison material, not patch-ready formatting. Ten initial label-context decisions are documented; the remaining manual accuracy review and live validation are still required. [DeepL comparison status](deepl-comparison-status.json)

The source/DeepL accuracy pass is complete for all 112 fields in the 56-record training table. The review retains the current English after checking every name and description, including point categories, partner Level versus XP, variable solo gains, boost durations and custom-player restrictions. The official 2026 Spirits labels support Focus, Pitch Type and Defense. The maintained review mappings and all 108 unique compiled lookups passed. English text, source records and the generated header are unchanged; the original draft JSON is retained as the historical drafting reference. Display-route and live-layout checks remain open. [Training accuracy validation](spirits-training-accuracy-validation.json)
