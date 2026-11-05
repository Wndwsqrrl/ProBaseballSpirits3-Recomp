@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
set "PATH=C:\Program Files\LLVM\bin;C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
cmake -S "%~dp0xex-inspect" -B "%~dp0..\local\inspector-build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=clang++ "-DCMAKE_PREFIX_PATH=D:/recomp-work/rexglue-sdk/out/install/win-amd64"
if errorlevel 1 exit /b %errorlevel%
cmake --build "%~dp0..\local\inspector-build" --parallel 4
exit /b %errorlevel%
