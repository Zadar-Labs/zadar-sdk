if(NOT TARGET zadar_webapi_cpp)
  message(STATUS "Skipping Zadar Web API C++ examples because the Web API SDK target was not built.")
  return()
endif()

set(ZADAR_WEBAPI_CPP_EXAMPLES
  sensor_info_example
  network_info_example
  start_stop_mode_example
  startup_mode_example
  configure_output_example
  ptp_configuration_example
  diagnostics_example
)

foreach(example_name IN LISTS ZADAR_WEBAPI_CPP_EXAMPLES)
  add_executable("${example_name}" "${example_name}.cpp")
  target_include_directories("${example_name}" PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
  target_link_libraries("${example_name}" PRIVATE zadar_webapi_cpp)
endforeach()
