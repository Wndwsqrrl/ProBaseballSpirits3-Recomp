# Known issues

This is a playable preview. The latest user test reports good gameplay performance, but a complete match, every mode and long-running seasons have not been exhaustively tested.

## Localization

- Some text still needs accuracy, formatting or name-reading review.
- Rare events, generated reports and unvisited branches can expose additional strings.
- Offline string and asset checks do not prove that every line fits its actual screen.
- Some generated player-name readings remain provisional.
- The original Japanese stadium signs, sponsor ads, ballpark artwork, logos and credits are intentionally preserved.

All 940 populated fields in the known Pennant event resource have English and a source/context review. That resource is only part of the game and does not establish whole-game completion.

## Gameplay and graphics

- Performance varies by hardware and scene. No locked-frame-rate claim is made.
- Rendering scales above native are experimental.
- Turning off presentation synchronization is not a verified high-frame-rate patch.
- Audio decoding warnings can occur; the underlying XMA decoding issue remains unresolved.
- Online services and platform dialogs are not verified as complete features of this Windows preview.

## Saves

English roster-name changes can be stored in game saves. The launcher therefore keeps English and Japanese saves separate. It does not migrate or convert existing development saves.

For the detailed investigation backlog, see the repository's [gap audit](https://github.com/Wndwsqrrl/ProBaseballSpirits3-Recomp/blob/main/translation/coverage-discovery.md) and [coverage status](https://github.com/Wndwsqrrl/ProBaseballSpirits3-Recomp/blob/main/translation/coverage-status.json).
