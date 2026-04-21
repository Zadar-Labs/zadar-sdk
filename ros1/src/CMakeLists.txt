cmake_minimum_required(VERSION 3.0.2)
project(zadar_udp_ros1_workspace)

set(CATKIN_TOPLEVEL TRUE)

set(_cmd "catkin_find_pkg" "catkin" "${CMAKE_SOURCE_DIR}")
execute_process(
  COMMAND ${_cmd}
  RESULT_VARIABLE _res
  OUTPUT_VARIABLE _out
  ERROR_VARIABLE _err
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_STRIP_TRAILING_WHITESPACE
)

if(NOT _res EQUAL 0 AND NOT _res EQUAL 2)
  string(REPLACE ";" " " _cmd_str "${_cmd}")
  message(FATAL_ERROR
    "Search for 'catkin' in workspace failed (${_cmd_str}): ${_err}")
endif()

if(_res EQUAL 0)
  set(catkin_EXTRAS_DIR "${CMAKE_SOURCE_DIR}/${_out}/cmake")
  include(${catkin_EXTRAS_DIR}/all.cmake NO_POLICY_SCOPE)
  add_subdirectory("${_out}")
else()
  if(NOT DEFINED CMAKE_PREFIX_PATH)
    if(NOT "$ENV{CMAKE_PREFIX_PATH}" STREQUAL "")
      if(NOT WIN32)
        string(REPLACE ":" ";" CMAKE_PREFIX_PATH $ENV{CMAKE_PREFIX_PATH})
      else()
        set(CMAKE_PREFIX_PATH $ENV{CMAKE_PREFIX_PATH})
      endif()
    endif()
  endif()

  set(catkin_search_path "")
  foreach(path ${CMAKE_PREFIX_PATH})
    if(EXISTS "${path}/.catkin")
      list(FIND catkin_search_path "${path}" _index)
      if(_index EQUAL -1)
        list(APPEND catkin_search_path "${path}")
      endif()
    endif()
  endforeach()

  set(CATKIN_TOPLEVEL_FIND_PACKAGE TRUE)
  find_package(catkin QUIET
    NO_POLICY_SCOPE
    PATHS ${catkin_search_path}
    NO_DEFAULT_PATH
    NO_CMAKE_FIND_ROOT_PATH)
  unset(CATKIN_TOPLEVEL_FIND_PACKAGE)

  if(NOT catkin_FOUND)
    message(FATAL_ERROR
      "find_package(catkin) failed. catkin was neither found in the workspace "
      "nor in CMAKE_PREFIX_PATH. Source the ROS environment before building.")
  endif()
endif()

catkin_workspace()
