param(
    [Parameter(Mandatory=$true)][string]$GameRoot,
    [string]$RexGlue='rexglue.exe'
)
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
$source=(Resolve-Path -LiteralPath $GameRoot).Path
$entry=Join-Path $source 'default.xex'
$expected='903E2E94188DA3525C9CA39B9F8D9F27C3F6BEEE25B93A48C90921CDA3D8CDC0'
if (-not (Test-Path -LiteralPath $entry -PathType Leaf)) { throw 'Supply an extracted Japanese Xbox 360 game containing default.xex.' }
if ((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash -ne $expected) { throw 'The executable does not match the supported Japanese release.' }
$command=Get-Command $RexGlue -ErrorAction Stop
$destination=Join-Path $workspace 'local/disc'
if ([IO.Path]::GetFullPath($source).TrimEnd('\','/') -ne [IO.Path]::GetFullPath($destination).TrimEnd('\','/')) {
    if (Test-Path -LiteralPath $destination) { throw 'local/disc already exists. Use it as GameRoot or choose a fresh checkout.' }
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Get-ChildItem -LiteralPath $source -Force | Copy-Item -Destination $destination -Recurse -Force
}
Push-Location (Join-Path $workspace 'prospi3-recomp')
try {
    & $command.Source codegen prospi3_manifest.toml
    if ($LASTEXITCODE -ne 0) { throw "Code generation failed: $LASTEXITCODE" }
} finally { Pop-Location }
Write-Output 'Code generation complete. Set REXGLUE_SDK_INSTALL and run tools/build-port.cmd.'
