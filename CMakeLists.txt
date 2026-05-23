cmake_minimum_required(VERSION 3.20)
project(arbiter VERSION 0.1.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 26)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build type with 4 modes
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags for different build types
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra -Wpedantic")
set(CMAKE_CXX_FLAGS_ASAN "-g -O1 -fsanitize=address -fsanitize=undefined -fno-sanitize-recover=all -Wall -Wextra -Wpedantic")
set(CMAKE_CXX_FLAGS_TSAN "-g -O1 -fsanitize=thread -Wall -Wextra -Wpedantic")

# Add custom build types
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS_${CMAKE_BUILD_TYPE}}")

# Include directories relative to project root
include_directories(${PROJECT_SOURCE_DIR})

# Fetch GTest
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG release-1.12.1
)
FetchContent_MakeAvailable(googletest)

# Enable clang-tidy
option(ENABLE_CLANG_TIDY "Enable clang-tidy" ON)
if(ENABLE_CLANG_TIDY)
    find_program(CLANG_TIDY clang-tidy)
    if(CLANG_TIDY)
        set(CMAKE_CXX_CLANG_TIDY "${CLANG_TIDY}")
    else()
        message(WARNING "clang-tidy not found")
    endif()
endif()

# Enable clang-format
option(ENABLE_CLANG_FORMAT "Enable clang-format" ON)
if(ENABLE_CLANG_FORMAT)
    find_program(CLANG_FORMAT clang-format)
    if(CLANG_FORMAT)
        file(GLOB_RECURSE ALL_SOURCE_FILES
            ${PROJECT_SOURCE_DIR}/*.cpp
            ${PROJECT_SOURCE_DIR}/*.hpp
            ${PROJECT_SOURCE_DIR}/*.h
        )
        list(FILTER ALL_SOURCE_FILES EXCLUDE REGEX ".*build/.*")
        list(FILTER ALL_SOURCE_FILES EXCLUDE REGEX ".*\.pb\..*")
        
        add_custom_target(format
            COMMAND ${CLANG_FORMAT} -i ${ALL_SOURCE_FILES}
            COMMENT "Running clang-format"
        )
        add_custom_target(check-format
            COMMAND ${CLANG_FORMAT} --dry-run --Werror ${ALL_SOURCE_FILES}
            COMMENT "Checking code formatting"
        )
    else()
        message(WARNING "clang-format not found")
    endif()
endif()

# Recursively add all subdirectories with CMakeLists.txt
file(GLOB SUBDIRS RELATIVE ${PROJECT_SOURCE_DIR} "*/CMakeLists.txt")
foreach(SUBDIR ${SUBDIRS})
    get_filename_component(DIR ${SUBDIR} DIRECTORY)
    add_subdirectory(${DIR})
endforeach()

# Enable testing
enable_testing()
