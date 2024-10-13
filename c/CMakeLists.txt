cmake_minimum_required(VERSION 3.14)

# Project Name and Language
project(TextEditor C)

# Set the C standard
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Enable FetchContent module
include(FetchContent)

# Declare the FetchContent dependency for raylib
FetchContent_Declare(
  raylib
  GIT_REPOSITORY https://github.com/raysan5/raylib.git
  GIT_TAG        4.5.0  # Specify the version/tag you want to use
)

# Make raylib available
FetchContent_MakeAvailable(raylib)

# Optionally, set raylib configurations before building
# For example, disable building examples and tests
set(BUILD_EXAMPLES OFF CACHE BOOL " " FORCE)
set(BUILD_GAMES OFF CACHE BOOL " " FORCE)
set(BUILD_SHARED_LIBS OFF CACHE BOOL " " FORCE)
set(RAYLIB_BUILD_EXAMPLES OFF CACHE BOOL " " FORCE)
set(RAYLIB_BUILD_GAMES OFF CACHE BOOL " " FORCE)

# Add the executable
add_executable(text_editor src/text_editor.c)

# Include raylib headers
target_include_directories(text_editor PRIVATE ${raylib_SOURCE_DIR}/src)

# Link raylib with the executable
target_link_libraries(text_editor PRIVATE raylib)

# Define any necessary preprocessor definitions
if(MSVC)
    target_compile_definitions(text_editor PRIVATE _CRT_SECURE_NO_WARNINGS)
endif()

# Platform-specific libraries
if(WIN32)
    target_link_libraries(text_editor PRIVATE opengl32 gdi32 winmm)
elseif(APPLE)
    find_library(COCOA_LIBRARY Cocoa REQUIRED)
    find_library(IOKIT_LIBRARY IOKit REQUIRED)
    find_library(COREVIDEO_LIBRARY CoreVideo REQUIRED)
    target_link_libraries(text_editor PRIVATE ${COCOA_LIBRARY} ${IOKIT_LIBRARY} ${COREVIDEO_LIBRARY})
elseif(UNIX)
    target_link_libraries(text_editor PRIVATE dl pthread m)
endif()

