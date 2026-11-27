param(
    [switch]$English,[switch]$Profile,[switch]$TraceText,[switch]$OriginalAssets,[switch]$AssetsOnly,
    [ValidateSet('720p','1080p','1440p','2160p')][string]$Resolution='720p',
    [ValidateRange(1,3)][int]$RenderScale=1,
    [switch]$NoVSync
)
$ErrorActionPreference = 'Stop'
if ($AssetsOnly -and ($English -or $OriginalAssets)) {
    throw 'AssetsOnly is a separate diagnostic mode; combine OriginalAssets with English for text-only testing.'
}
$workspace = Split-Path -Parent $PSScriptRoot
$portDir = Join-Path $workspace 'prospi3-recomp\out\build\win-amd64-release'
$gameRoot = Join-Path $workspace 'local\disc'
if (($English -and -not $OriginalAssets) -or $AssetsOnly) {
    $gameRoot = Join-Path $workspace 'local\english-disc'
    if (-not (Test-Path -LiteralPath (Join-Path $gameRoot 'cdvdroot\baseball.fbd'))) {
        throw 'Build the English asset tree with tools/build-english-assets.py first.'
    }
}
$env:PROSPI3_ENGLISH = if ($English) { '1' } else { '0' }
$env:PROSPI3_PROFILE = if ($Profile) { '1' } else { '0' }
$env:PROSPI3_TRACE_TEXT = if ($TraceText) { '1' } else { '0' }
$env:PROSPI3_RELOCATE_TEXT = '0'
$env:PROSPI3_PROFILE_LABEL = if ($AssetsOnly) { 'english-assets-only' } elseif ($English -and $OriginalAssets) { 'english-text-only' } elseif ($English) { 'english-full' } else { 'japanese' }
if ($Resolution -ne '720p' -or $RenderScale -ne 1 -or $NoVSync) {
    $env:PROSPI3_PROFILE_LABEL += "-$Resolution-${RenderScale}x"
    if ($NoVSync) { $env:PROSPI3_PROFILE_LABEL += '-unlocked' }
}
$graphicsArgs=@("--resolution=$Resolution","--resolution_scale=$RenderScale")
if ($NoVSync) { $graphicsArgs+='--vsync=false' }
& (Join-Path $portDir 'prospi3.exe') "--game_data_root=$gameRoot" `
    "--user_data_root=$(Join-Path $workspace 'local\userdata')" `
    "--cache_root=$(Join-Path $workspace 'local\cache')" `
    '--gpu_backend=d3d12' '--render_target_path_d3d12=rov' '--mnk_mode=true' @graphicsArgs
