# Preparing a Windows preview

Use a verified native build and a separately verified English asset tree. Do not package an original game dump, saves, caches or development traces.

## Build the launcher and asset delta

```powershell
./tools/build-launcher.ps1 -OutputDirectory local/release-prep/stage
python tools/build-release-patch.py local/disc/cdvdroot/baseball.fbd local/english-disc/cdvdroot/baseball.fbd local/release-prep/english-assets.p3patch --report local/release-prep/english-assets-manifest.json
```

The delta stores compressed XOR differences for decoded changed members and copy instructions for unchanged members. Applying it requires the exact original archive. Source and reconstructed archive hashes are checked before installation completes.

Place the verified `prospi3.exe`, `rexruntime.dll` and `rexgpu-xenos.dll` in `stage/bin/`, and the delta in `stage/assets/english-assets.p3patch`. Keep matching third-party notices under `licenses/`.

## Verify

The launcher has background checks that do not launch the game:

- `--self-test REPORT`: defaults, both language plans, separate save profiles, quoting, runtime requirements and rejected settings.
- `--verify-patch ORIGINAL_ARCHIVE OUTPUT_ARCHIVE REPORT`: reconstruct the archive and verify the result.
- `--check-install ORIGINAL_GAME_FOLDER REPORT`: validate the supported executable, prepare English files and check cache reuse.
- `--preview IMAGE`: render the launcher without showing its window.

Use a synthetic fixture for cancellation and malformed-input checks. Verify that the original game files remain unchanged. Live launcher-to-game behavior and gameplay still need their own checks; these background checks do not replace them.

## Package

```powershell
python tools/package-release.py --stage local/release-prep/stage --version v0.1.0-preview.1 --output local/releases/ProSpi3-Recomp-v0.1.0-preview.1-win64.zip
```

The packager uses an explicit allowlist, verifies every ZIP entry against its checksum, and writes `SHA256SUMS.txt`. It excludes `local/`, saves, caches, original executables and game archives.

Prepare the release notes from `docs/releases/`, attach the verified ZIP and checksums, and keep the GitHub release as a draft until it is ready to publish. Repository visibility is a separate setting.
