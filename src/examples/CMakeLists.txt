cmake_minimum_required (VERSION 3.0)
cmake_policy (SET CMP0048 NEW)

project (glfw_example
    VERSION 0.0.1
    LANGUAGES C CXX)

# Set a default build type if none was specified
set (CMAKE_BUILD_TYPE_DEFAULT "Debug")
if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    message (STATUS "Setting build type to ${CMAKE_BUILD_TYPE_DEFAULT} as none was specified.")
    set (CMAKE_BUILD_TYPE ${CMAKE_BUILD_TYPE_DEFAULT} CACHE STRING "Choose the type of build." FORCE)
    # Set the possible values of build type for cmake-gui
    set_property (CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release"
        "MinSizeRel" "RelWithDebInfo")
endif ()

# Add the main library
add_executable (${PROJECT_NAME} glfw_example1.cpp)

# Try to set compiler flags for the library
include (CheckCXXCompilerFlag)
set (ADDITIONAL_FLAGS "-std=c++11;-Wall;-Wextra;-pedantic;-fexceptions")
foreach (flag ${ADDITIONAL_FLAGS})
    check_cxx_compiler_flag (${flag} compiler_supports_flag)
    if (compiler_supports_flag)
        target_compile_options (${PROJECT_NAME} PUBLIC ${flag})
    else ()
        message (WARNING "Compiler does not support the flag ${flag}")
    endif ()
endforeach ()

find_package(PkgConfig REQUIRED)
if (PKGCONFIG_FOUND)
    pkg_search_module(GLFW REQUIRED glfw3)

    if (GLFW_FOUND)
        #target_include_directories(${PROJECT_NAME} PRIVATE ${GLFW_INCLUDE_DIRS})
        target_link_libraries(${PROJECT_NAME} PRIVATE ${GLFW_LIBRARIES})
    endif ()
endif()

find_package(OpenGL REQUIRED)
if (OPENGL_FOUND)
    #target_include_directories(${PROJECT_NAME} PRIVATE ${OPENGL_INCLUDE_DIRS})
    target_link_libraries(${PROJECT_NAME} PRIVATE ${OPENGL_LIBRARIES})
endif ()
