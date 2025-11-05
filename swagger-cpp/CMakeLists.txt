cmake_minimum_required(VERSION 3.15)
project(swagger_cpp VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -O3")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -O0")

# Find required packages
find_package(OpenCV REQUIRED)

# Include directories
include_directories(
    ${PROJECT_SOURCE_DIR}/include
    ${OpenCV_INCLUDE_DIRS}
)

# Source files
set(SOURCES
    src/main.cpp
    src/graph.cpp
    src/utils.cpp
    src/step1_preprocess.cpp
    src/step2_skeleton.cpp
    src/skeleton_loader.cpp
    src/step3_boundary.cpp
    src/step4_free_space.cpp
    src/step5_delaunay.cpp
    src/step6_prune.cpp
    src/file_writer.cpp
)

# Main executable
add_executable(generate_graph ${SOURCES})

# Link libraries
target_link_libraries(generate_graph
    ${OpenCV_LIBS}
)

# Install
install(TARGETS generate_graph DESTINATION bin)

# Add examples subdirectory
add_subdirectory(examples)
