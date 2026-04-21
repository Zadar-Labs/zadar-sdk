cmake_minimum_required(VERSION 3.16)
project(zadar_udp_driver LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(CURL REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(Protobuf REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(zadar_msgs REQUIRED)

get_filename_component(ZADAR_UDP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)
set(ZADAR_SDK_CPP_INCLUDE_DIR "${ZADAR_UDP_ROOT}/sdk/cpp/zadar_udp/include")
set(ZADAR_SDK_CPP_SRC_DIR "${ZADAR_UDP_ROOT}/sdk/cpp/zadar_udp/src")
set(ZADAR_WEBAPI_CPP_INCLUDE_DIR "${ZADAR_UDP_ROOT}/sdk/cpp/zadar_webapi/include")
set(ZADAR_WEBAPI_CPP_SRC_DIR "${ZADAR_UDP_ROOT}/sdk/cpp/zadar_webapi/src")
set(ZADAR_PROTO_DIR "${ZADAR_UDP_ROOT}/proto")
set(ZADAR_PROTO_FILE "${ZADAR_PROTO_DIR}/ZadarFrame.proto")
set(ZADAR_PROTO_INPUT_FILE "ZadarFrame.proto")
set(ZADAR_GENERATED_CPP_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated/cpp")
set(ZADAR_GENERATED_PROTO_SRC "${ZADAR_GENERATED_CPP_DIR}/ZadarFrame.pb.cc")
set(ZADAR_GENERATED_PROTO_HDR "${ZADAR_GENERATED_CPP_DIR}/ZadarFrame.pb.h")

set(ZADAR_PROTOC_EXECUTABLE "${Protobuf_PROTOC_EXECUTABLE}")
if(NOT ZADAR_PROTOC_EXECUTABLE)
  find_program(ZADAR_PROTOC_EXECUTABLE protoc)
endif()

if(NOT ZADAR_PROTOC_EXECUTABLE)
  message(FATAL_ERROR "Unable to locate protoc. Install protobuf-compiler or make protoc available in PATH.")
endif()

if(NOT EXISTS "${ZADAR_PROTO_DIR}")
  message(FATAL_ERROR "Unable to locate proto directory at ${ZADAR_PROTO_DIR}")
endif()

if(NOT EXISTS "${ZADAR_PROTO_FILE}")
  message(FATAL_ERROR "Unable to locate protobuf schema at ${ZADAR_PROTO_FILE}")
endif()

add_custom_command(
  OUTPUT
    "${ZADAR_GENERATED_PROTO_SRC}"
    "${ZADAR_GENERATED_PROTO_HDR}"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${ZADAR_GENERATED_CPP_DIR}"
  COMMAND "${CMAKE_COMMAND}" -E chdir "${ZADAR_PROTO_DIR}"
    "${ZADAR_PROTOC_EXECUTABLE}"
    --proto_path=.
    --cpp_out=${ZADAR_GENERATED_CPP_DIR}
    "${ZADAR_PROTO_INPUT_FILE}"
  DEPENDS "${ZADAR_PROTO_FILE}"
  VERBATIM
)

add_custom_target(
  zadar_udp_driver_proto_gen
  DEPENDS
    "${ZADAR_GENERATED_PROTO_SRC}"
    "${ZADAR_GENERATED_PROTO_HDR}"
)

add_executable(zadar_udp_driver_node
  src/node.cpp
  "${ZADAR_SDK_CPP_SRC_DIR}/radar_listener.cpp"
  "${ZADAR_SDK_CPP_SRC_DIR}/imu_listener.cpp"
  "${ZADAR_WEBAPI_CPP_SRC_DIR}/client.cpp"
  "${ZADAR_WEBAPI_CPP_SRC_DIR}/driver_control.cpp"
  "${ZADAR_GENERATED_PROTO_SRC}"
)

add_dependencies(zadar_udp_driver_node zadar_udp_driver_proto_gen)

target_include_directories(zadar_udp_driver_node
  PRIVATE
    "${ZADAR_SDK_CPP_INCLUDE_DIR}"
    "${ZADAR_WEBAPI_CPP_INCLUDE_DIR}"
    "${ZADAR_GENERATED_CPP_DIR}"
)

target_link_libraries(zadar_udp_driver_node
  PUBLIC
    ${geometry_msgs_TARGETS}
    ${sensor_msgs_TARGETS}
    ${std_msgs_TARGETS}
    ${zadar_msgs_TARGETS}
    CURL::libcurl
    rclcpp::rclcpp
    sensor_msgs::sensor_msgs_library
)

if(TARGET protobuf::libprotobuf)
  target_link_libraries(zadar_udp_driver_node PRIVATE protobuf::libprotobuf)
else()
  target_include_directories(zadar_udp_driver_node PRIVATE "${Protobuf_INCLUDE_DIRS}")
  target_link_libraries(zadar_udp_driver_node PRIVATE "${Protobuf_LIBRARIES}")
endif()

install(TARGETS zadar_udp_driver_node
  DESTINATION lib/${PROJECT_NAME}
)

install(FILES README.md
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
