cmake_minimum_required(VERSION 3.16)
project(zadar_udp_customer_examples LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(
  ZADAR_BUILD_WEBAPI_CPP
  "Build the C++ Web API SDK and examples (requires CURL/libcurl)."
  ON
)

add_subdirectory(sdk/cpp)
add_subdirectory(examples/cpp)
