@echo off

:: Define raylib include and library paths for vcpkg installed via Scoop
:: Adjust these paths if your vcpkg installation is different
set RAYLIB_INCLUDE=%USERPROFILE%\scoop\apps\vcpkg\current\installed\x64-windows\include
set RAYLIB_LIB=%USERPROFILE%\scoop\apps\vcpkg\current\installed\x64-windows\lib

:: Define Zig compiler (adjust if Zig is not in your PATH)
set ZIG_CC=zig cc

:: Create the dlls directory if it doesn't exist
if not exist dlls mkdir dlls

:: Compile the Tixy DLL
%ZIG_CC% -target x86_64-windows-gnu -shared -o dlls\tixy.dll tixy.c -I %RAYLIB_INCLUDE% -L %RAYLIB_LIB% -lraylib

:: Compile the Infinite Canvas application
%ZIG_CC% -target x86_64-windows-gnu -o infinite_canvas.exe main.c -I %RAYLIB_INCLUDE% -L %RAYLIB_LIB% -lraylib -luser32 -lgdi32 -lshell32 -lwinmm

:: Indicate build completion
echo Build complete.
