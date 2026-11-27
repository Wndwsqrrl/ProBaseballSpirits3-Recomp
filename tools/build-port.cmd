@echo off
setlocal
if not defined REXGLUE_SDK_INSTALL (
  echo Set REXGLUE_SDK_INSTALL to your installed ReXGlue SDK directory.
  exit /b 1
)
set "PROSPI3_VS_ROOT=%VSINSTALLDIR%"
if not defined PROSPI3_VS_ROOT (
  if not exist "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" (
    echo Visual Studio 2022 C++ build tools were not found.
    exit /b 1
  )
  for /f "usebackq delims=" %%I in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "PROSPI3_VS_ROOT=%%I"
)
if not exist "%PROSPI3_VS_ROOT%\VC\Auxiliary\Build\vcvars64.bat" (
  echo Visual Studio C++ x64 tools were not found.
  exit /b 1
)
call "%PROSPI3_VS_ROOT%\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
if exist "%ProgramFiles%\LLVM\bin\clang++.exe" set "PATH=%ProgramFiles%\LLVM\bin;%PATH%"
set "PATH=%PROSPI3_VS_ROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
pushd "%~dp0..\prospi3-recomp"
cmake --preset win-amd64-release "-DCMAKE_PREFIX_PATH=%REXGLUE_SDK_INSTALL%"
if errorlevel 1 exit /b %errorlevel%
cmake --build --preset win-amd64-release --parallel 2
set "PROSPI3_BUILD_RESULT=%errorlevel%"
popd
exit /b %PROSPI3_BUILD_RESULT%
