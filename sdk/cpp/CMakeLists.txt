cmake_minimum_required(VERSION 3.16)
project(zadar_udp_sdk LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(zadar_udp)

if(ZADAR_BUILD_WEBAPI_CPP)
  add_subdirectory(zadar_webapi)
else()
  message(STATUS "Skipping Zadar Web API C++ SDK because ZADAR_BUILD_WEBAPI_CPP=OFF.")
endif()
