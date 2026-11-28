cmake_minimum_required(VERSION 3.16)
project(sauria_systemc CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(SystemCLanguage CONFIG REQUIRED)

# PE core library
add_library(pe_lib STATIC
    src/pe.cpp
)
target_include_directories(pe_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(pe_lib PUBLIC SystemC::systemc)

# tb_pe testbench
add_executable(tb_pe
    tb/tb_pe.cpp
)
target_link_libraries(tb_pe PRIVATE pe_lib)

# CTest integration
enable_testing()
add_test(NAME tb_pe COMMAND tb_pe)