#!/usr/bin/env python3
"""
Kit - Project configuration utility for C++ projects
Handles automatic CMakeLists.txt generation and module configuration
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Set, Optional


class KitConfig:
    """Configuration for kit utility"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.source_extensions = {'.cpp', '.cc', '.cxx', '.c'}
        self.header_extensions = {'.hpp', '.h', '.hxx', '.hh'}
        self.test_pattern = '_test.cpp'
    
    def find_source_files(self, directory: Path) -> List[Path]:
        """Find all source files in directory"""
        sources = []
        for ext in self.source_extensions:
            sources.extend(directory.glob(f'*{ext}'))
        return sorted(sources)
    
    def find_header_files(self, directory: Path) -> List[Path]:
        """Find all header files in directory"""
        headers = []
        for ext in self.header_extensions:
            headers.extend(directory.glob(f'*{ext}'))
        return sorted(headers)
    
    def find_test_files(self, directory: Path) -> List[Path]:
        """Find all test files in directory"""
        return sorted(directory.glob(f'*{self.test_pattern}'))
    
    def find_submodules(self, directory: Path) -> List[Path]:
        """Find all submodules (directories with CMakeLists.txt or source files)"""
        submodules = []
        for item in directory.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it has CMakeLists.txt or source files
                cmake_file = item / 'CMakeLists.txt'
                has_sources = any(item.glob(f'*{ext}') for ext in self.source_extensions)
                if cmake_file.exists() or has_sources:
                    submodules.append(item)
        return sorted(submodules)
    
    def get_module_name(self, directory: Path) -> str:
        """Generate module name from directory path"""
        relative = directory.relative_to(self.root_dir)
        return str(relative).replace('/', '_')


def generate_cmake_lists(config: KitConfig, directory: Path, is_root: bool = False) -> str:
    """Generate CMakeLists.txt content for a directory"""
    
    module_name = config.get_module_name(directory)
    sources = config.find_source_files(directory)
    headers = config.find_header_files(directory)
    tests = config.find_test_files(directory)
    submodules = config.find_submodules(directory)
    
    if is_root:
        # Root CMakeLists.txt - use regular string to avoid f-string conflicts
        return """cmake_minimum_required(VERSION 3.20)
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
        list(FILTER ALL_SOURCE_FILES EXCLUDE REGEX ".*\\.pb\\..*")
        
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
"""
    else:
        # Module CMakeLists.txt
        cmake_content = []
        
        cmake_content.append(f"# Module: {module_name}")
        cmake_content.append("")
        
        # Only create library if we have sources
        if sources:
            cmake_content.append("# Source files")
            cmake_content.append(f"set({module_name}_SOURCES")
            for source in sources:
                cmake_content.append(f'    "{source.name}"')
            cmake_content.append(")")
            cmake_content.append("")
            
            cmake_content.append("# Create library for this module")
            cmake_content.append(f"add_library({module_name} ${{{module_name}_SOURCES}})")
            cmake_content.append("")
            
            cmake_content.append("# Set include directories (relative to project root)")
            cmake_content.append("target_include_directories({module_name} PUBLIC".format(module_name=module_name))
            cmake_content.append("    ${PROJECT_SOURCE_DIR}")
            cmake_content.append(")")
            cmake_content.append("")
            
            # Add dependencies section as comment
            cmake_content.append("# Link dependencies")
            cmake_content.append("# target_link_libraries({module_name} PUBLIC".format(module_name=module_name))
            cmake_content.append("#     other_module")
            cmake_content.append("# )")
            cmake_content.append("")
        else:
            cmake_content.append("# No source files in this module yet")
            cmake_content.append("# Add .cpp files to enable library creation")
            cmake_content.append("")
        
        # Add tests
        if tests:
            cmake_content.append("# Tests")
            for test in tests:
                test_name = test.stem
                cmake_content.append(f'add_executable({test_name} "{test.name}")')
                if sources:
                    cmake_content.append("target_link_libraries({test_name}".format(test_name=test_name))
                    cmake_content.append(f"    {module_name}")
                    cmake_content.append("    GTest::gtest")
                    cmake_content.append("    GTest::gtest_main")
                    cmake_content.append(")")
                else:
                    cmake_content.append("target_link_libraries({test_name}".format(test_name=test_name))
                    cmake_content.append("    GTest::gtest")
                    cmake_content.append("    GTest::gtest_main")
                    cmake_content.append(")")
                cmake_content.append("add_test(NAME {test_name} COMMAND {test_name})".format(test_name=test_name))
                cmake_content.append("")
        else:
            cmake_content.append("# No tests found")
            cmake_content.append("# Create *_test.cpp files to add tests")
            cmake_content.append("")
        
        return '\n'.join(cmake_content)


def configure_directory(config: KitConfig, directory: Path, is_root: bool = False) -> None:
    """Configure a directory and its submodules"""
    
    print(f"Configuring: {directory.relative_to(config.root_dir)}")
    
    # Generate CMakeLists.txt
    cmake_content = generate_cmake_lists(config, directory, is_root)
    cmake_file = directory / 'CMakeLists.txt'
    
    # Write file
    cmake_file.write_text(cmake_content)
    print(f"  ✓ Generated {cmake_file.relative_to(config.root_dir)}")
    
    # Recursively configure submodules
    if not is_root:
        submodules = config.find_submodules(directory)
        for submodule in submodules:
            configure_directory(config, submodule, is_root=False)


def cmd_cfg(args):
    """Handle cfg command"""
    root_dir = Path(args.directory).resolve()
    
    if not root_dir.exists():
        print(f"Error: Directory {root_dir} does not exist")
        sys.exit(1)
    
    config = KitConfig(root_dir)
    
    print(f"Configuring project in: {root_dir}")
    print("-" * 50)
    
    # Configure root and all submodules
    configure_directory(config, root_dir, is_root=True)
    
    print("-" * 50)
    print("✓ Configuration complete!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Kit - Project configuration utility for C++ projects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kit cfg                    # Configure current directory
  kit cfg /path/to/project   # Configure specific directory
  kit cfg --recursive        # Configure recursively (default behavior)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # cfg command
    cfg_parser = subparsers.add_parser('cfg', help='Configure project modules')
    cfg_parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Project directory (default: current directory)'
    )
    cfg_parser.add_argument(
        '--recursive',
        action='store_true',
        default=True,
        help='Configure recursively (default: True)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'cfg':
        cmd_cfg(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
