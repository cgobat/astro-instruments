cmake_minimum_required(VERSION 3.0)
PROJECT(indi_rpicam2 CXX C)

LIST(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../../cmake_modules/")

include(GNUInstallDirs)

set (INDI_RPICAM2_VERSION_MAJOR 0)
set (INDI_RPICAM2_VERSION_MINOR 1)

find_package(CFITSIO REQUIRED)
find_package(INDI REQUIRED)
find_package(ZLIB REQUIRED)

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.h.cmake ${CMAKE_CURRENT_BINARY_DIR}/config.h )
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/indi_rpicam2.xml.cmake ${CMAKE_CURRENT_BINARY_DIR}/indi_rpicam2.xml )

include_directories( ${CMAKE_CURRENT_BINARY_DIR})
include_directories( ${CMAKE_CURRENT_SOURCE_DIR})
include_directories( ${INDI_INCLUDE_DIR})
include_directories( ${CFITSIO_INCLUDE_DIR})

include(CMakeCommon)

############# GENERIC CCD ###############
set(indi_rpicam2_SRCS
        ${CMAKE_CURRENT_SOURCE_DIR}/rpicam2.cpp
)

add_executable(indi_rpicam2 ${indi_rpicam2_SRCS})

target_link_libraries(indi_rpicam2 ${INDI_LIBRARIES} ${CFITSIO_LIBRARIES} m ${ZLIB_LIBRARY})

install(TARGETS indi_rpicam2 RUNTIME DESTINATION bin)

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/indi_rpicam2.xml DESTINATION ${INDI_DATA_DIR})
