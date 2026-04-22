set(ZADAR_CPP_EXAMPLES
  radar_data_example
  clusters_example
  tracks_example
  odometry_example
  imu_data_example
)

foreach(example_name IN LISTS ZADAR_CPP_EXAMPLES)
  add_executable("${example_name}" "${example_name}.cpp")
  target_include_directories("${example_name}" PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
  target_link_libraries("${example_name}" PRIVATE zadar_udp_cpp)
endforeach()
