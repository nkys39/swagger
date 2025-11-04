cmake_minimum_required(VERSION 3.15)

find_package(OpenCV REQUIRED)

add_executable(create_sample_map create_sample_map.cpp)
target_link_libraries(create_sample_map ${OpenCV_LIBS})
