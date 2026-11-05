param(
    [Parameter(Mandatory = $true)][string]$GameRoot,
    [string]$RexGlue = 'D:\recomp-work\rexglue-sdk\out\install\win-amd64\bin\rexglue.exe'
)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$resolvedGameRoot = (Resolve-Path -LiteralPath $GameRoot).Path
if (-not (Test-Path -LiteralPath $resolvedGameRoot -PathType Container)) {
    throw 'GameRoot must be an extracted game directory.'
}
$entrypoint = Join-Path $resolvedGameRoot 'default.xex'
if (-not (Test-Path -LiteralPath $entrypoint -PathType Leaf)) {
    throw 'No default.xex found at GameRoot. Supply the extracted Xbox 360 game directory.'
}
if (-not (Test-Path -LiteralPath $RexGlue -PathType Leaf)) {
    throw "ReXGlue executable not found: $RexGlue"
}
$project = Join-Path $workspace 'prospi3-recomp'
if (Test-Path -LiteralPath $project) {
    throw "Project directory already exists; inspect it before regenerating: $project"
}
$reports = Join-Path $workspace 'local'
New-Item -ItemType Directory -Path $reports -Force | Out-Null
$rootPrefix = $resolvedGameRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
Get-ChildItem -LiteralPath $resolvedGameRoot -File -Recurse | ForEach-Object {
    [pscustomobject]@{
        Path = $_.FullName.Substring($rootPrefix.Length)
        Bytes = $_.Length
        Extension = $_.Extension
    }
} | Export-Csv -LiteralPath (Join-Path $reports 'disc-inventory.csv') -NoTypeInformation -Encoding UTF8
Get-FileHash -LiteralPath $entrypoint -Algorithm SHA256 |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $reports 'entrypoint-sha256.json') -Encoding UTF8
& $RexGlue init --project-name prospi3 --xex-path $entrypoint --game-root $resolvedGameRoot --project-root $project --scan-dll
if ($LASTEXITCODE -ne 0) { throw "ReXGlue init failed with exit code $LASTEXITCODE" }
Write-Output "Project generated at $project. Inventory and executable hash are in $reports."
