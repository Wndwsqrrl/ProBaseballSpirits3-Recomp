param([string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $workspace 'local\release-prep\stage' }
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'The Windows .NET Framework C# compiler is required.' }
$output = Join-Path $OutputDirectory 'ProSpi3 Launcher.exe'
$logo = Join-Path $workspace 'launcher\assets\title-atlas.png'
$iconPath = Join-Path $OutputDirectory 'launcher.ico'
Add-Type -AssemblyName System.Drawing
if (-not ('ProSpi3.IconHandle' -as [type])) {
    Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; namespace ProSpi3 { public static class IconHandle { [DllImport("user32.dll")] public static extern bool DestroyIcon(IntPtr handle); } }'
}
$atlas = [Drawing.Image]::FromFile($logo)
$bitmap = [Drawing.Bitmap]::new(256,256)
$graphics = [Drawing.Graphics]::FromImage($bitmap)
try {
    $graphics.Clear([Drawing.Color]::Transparent)
    $graphics.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.DrawImage($atlas,[Drawing.Rectangle]::new(18,0,220,256),[Drawing.Rectangle]::new(640,4,172,200),[Drawing.GraphicsUnit]::Pixel)
    $handle = $bitmap.GetHicon()
    $icon = [Drawing.Icon]::FromHandle($handle)
    $stream = [IO.File]::Create($iconPath)
    try { $icon.Save($stream) } finally { $stream.Dispose(); $icon.Dispose(); [ProSpi3.IconHandle]::DestroyIcon($handle) | Out-Null }
} finally { $graphics.Dispose(); $bitmap.Dispose(); $atlas.Dispose() }
& $compiler /nologo /target:winexe /platform:x64 /optimize+ /codepage:65001 `
    "/out:$output" "/win32manifest:$(Join-Path $workspace 'launcher\app.manifest')" "/win32icon:$iconPath" "/resource:$logo,ProSpi3.title-atlas.png" `
    /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll `
    /reference:System.IO.Compression.dll (Join-Path $workspace 'launcher\ReleaseFiles.cs') (Join-Path $workspace 'launcher\Program.cs') (Join-Path $workspace 'launcher\BrandHeader.cs')
if ($LASTEXITCODE -ne 0) { throw "Launcher compilation failed: $LASTEXITCODE" }
Write-Output "Built $output"
