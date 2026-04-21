find_package(CURL QUIET)

if(NOT CURL_FOUND)
  message(FATAL_ERROR
    "CURL was not found. Install libcurl4-openssl-dev to build the C++ Web API "
    "SDK/examples, or configure with -DZADAR_BUILD_WEBAPI_CPP=OFF."
  )
endif()

add_library(zadar_webapi_cpp
  src/client.cpp
  src/driver_control.cpp
)

target_include_directories(zadar_webapi_cpp
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(zadar_webapi_cpp
  PUBLIC
    CURL::libcurl
)
