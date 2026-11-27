# Getting started

## Requirements

- Windows x64 with Direct3D 12 support.
- .NET Framework 4.8 and the [Microsoft Visual C++ x64 Runtime](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist). These are runtime requirements; Visual Studio is not needed to play.
- Your own extracted Japanese Xbox 360 copy of Pro Yakyuu Spirits 3.
- Enough free space for a separate English archive, approximately 1.6 GB plus the other extracted game files.

The current build has been tested on NVIDIA graphics. Other graphics configurations need further testing. Start with 720p and native rendering scale.

If the launcher reports a missing C++ runtime, use its **Install required runtime** link to get Microsoft's installer, then try again.

## Launch

Extract the preview package to a writable folder and open **ProSpi3 Launcher.exe**. Select the extracted game folder containing `default.xex`; do not select an ISO file or the `cdvdroot` subfolder.

Choose a language and select **Play**. English is the default. The first English launch prepares localized files and verifies the result before starting the game. Later launches reuse those files when the installation is unchanged.

Japanese uses your original extracted files. Switching language takes effect on the next launch and keeps separate saves for each language.

## Controls

An Xbox-compatible controller is recommended. The port also includes these keyboard shortcuts:

| Xbox input | Keyboard |
| --- | --- |
| D-pad | Arrow keys or W / A / S / D |
| A / confirm | Space |
| B / back | Backspace |
| X | L |
| Y | P |
| Start | Enter |
| Back | Tab or Z |
| Left / right bumper | 1 / 3 |

These shortcuts do not replace a controller for every analog gameplay action.

## Saves and logs

The launcher stores settings, generated English files, saves, logs and caches under `local/` beside the launcher. English and Japanese use separate user-data folders. Back up your saves before moving between releases.

Existing development saves are not moved automatically. Keep the old `local/userdata` directory if you have used the source checkout before.

## Graphics

Use the default 720p output and native rendering scale for an initial check. Output resolution changes the window size; rendering scale changes internal draw resolution. Higher scales are experimental and can reduce performance. They do not increase the game's simulation frame rate.

The port prefers an available NVIDIA adapter. Check the startup log if the game selects an unexpected GPU.

See [known issues](known-issues.md) for current limits, or [building from source](https://github.com/Wndwsqrrl/ProBaseballSpirits3-Recomp/blob/main/docs/building.md) for the development workflow.
