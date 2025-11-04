cmake_minimum_required(VERSION 3.15)
project(swagger_minimal VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -O3")

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
    src/map_processor.cpp
    src/boundary_sampler.cpp
    src/file_writer.cpp
)

# Executable
add_executable(process_map ${SOURCES})

# Link libraries
target_link_libraries(process_map
    ${OpenCV_LIBS}
)

# Install
install(TARGETS process_map DESTINATION bin)

# Add examples subdirectory
add_subdirectory(examples)
