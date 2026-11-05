@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
set "PATH=C:\Program Files\LLVM\bin;C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
pushd "%~dp0..\prospi3-recomp"
if not defined REXGLUE_SDK_INSTALL set "REXGLUE_SDK_INSTALL=D:/recomp-work/rexglue-sdk/out/install/win-amd64"
cmake --preset win-amd64-release "-DCMAKE_PREFIX_PATH=%REXGLUE_SDK_INSTALL%"
if errorlevel 1 exit /b %errorlevel%
cmake --build --preset win-amd64-release --parallel 6
exit /b %errorlevel%
