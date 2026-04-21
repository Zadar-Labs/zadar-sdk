if(EXISTS "/usr/bin/protoc")
  set(Protobuf_PROTOC_EXECUTABLE "/usr/bin/protoc" CACHE FILEPATH "Preferred protoc executable" FORCE)
endif()

find_package(Protobuf QUIET)

set(ZADAR_PROTOBUF_TARGET "")
set(ZADAR_PROTOBUF_INCLUDE_DIR "")
set(ZADAR_PROTOBUF_LIBRARY "")

if(Protobuf_FOUND)
  if(TARGET protobuf::libprotobuf)
    set(ZADAR_PROTOBUF_TARGET protobuf::libprotobuf)
  else()
    set(ZADAR_PROTOBUF_INCLUDE_DIR "${Protobuf_INCLUDE_DIRS}")
    set(ZADAR_PROTOBUF_LIBRARY "${Protobuf_LIBRARIES}")
  endif()
else()
  find_program(ZADAR_PROTOC_EXECUTABLE protoc)
  set(ZADAR_PROTOBUF_HINTS "")
  if(DEFINED ENV{CONDA_PREFIX})
    list(APPEND ZADAR_PROTOBUF_HINTS "$ENV{CONDA_PREFIX}")
  endif()
  if(ZADAR_PROTOC_EXECUTABLE)
    get_filename_component(ZADAR_PROTOC_BIN_DIR "${ZADAR_PROTOC_EXECUTABLE}" DIRECTORY)
    get_filename_component(ZADAR_PROTOBUF_PREFIX "${ZADAR_PROTOC_BIN_DIR}/.." ABSOLUTE)
    list(APPEND ZADAR_PROTOBUF_HINTS "${ZADAR_PROTOBUF_PREFIX}")
  endif()

  list(PREPEND CMAKE_PREFIX_PATH ${ZADAR_PROTOBUF_HINTS})
  find_package(protobuf CONFIG QUIET)

  if(protobuf_FOUND)
    set(ZADAR_PROTOBUF_TARGET protobuf::libprotobuf)
  else()
    find_path(
      ZADAR_PROTOBUF_INCLUDE_DIR
      NAMES google/protobuf/message.h
      HINTS ${ZADAR_PROTOBUF_HINTS}
      PATH_SUFFIXES include
    )

    find_library(
      ZADAR_PROTOBUF_LIBRARY
      NAMES protobuf libprotobuf
      HINTS ${ZADAR_PROTOBUF_HINTS}
      PATH_SUFFIXES lib
    )

    if(NOT ZADAR_PROTOBUF_INCLUDE_DIR OR NOT ZADAR_PROTOBUF_LIBRARY)
      message(FATAL_ERROR "Unable to locate protobuf headers and library. Install libprotobuf-dev or set CONDA_PREFIX to a compatible protobuf toolchain.")
    endif()
  endif()
endif()

get_filename_component(ZADAR_UDP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)
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
  zadar_udp_cpp_proto_gen
  DEPENDS
    "${ZADAR_GENERATED_PROTO_SRC}"
    "${ZADAR_GENERATED_PROTO_HDR}"
)

add_library(zadar_udp_cpp STATIC
  src/radar_listener.cpp
  src/imu_listener.cpp
  "${ZADAR_GENERATED_PROTO_SRC}"
)

add_dependencies(zadar_udp_cpp zadar_udp_cpp_proto_gen)

target_include_directories(zadar_udp_cpp
  PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${ZADAR_GENERATED_CPP_DIR}"
)

if(ZADAR_PROTOBUF_TARGET)
  target_link_libraries(zadar_udp_cpp PUBLIC "${ZADAR_PROTOBUF_TARGET}")
else()
  target_include_directories(zadar_udp_cpp PUBLIC "${ZADAR_PROTOBUF_INCLUDE_DIR}")
  target_link_libraries(zadar_udp_cpp PUBLIC "${ZADAR_PROTOBUF_LIBRARY}")
endif()
