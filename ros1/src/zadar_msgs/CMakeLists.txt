cmake_minimum_required(VERSION 3.0.2)
project(zadar_msgs)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  message_generation
  sensor_msgs
  std_msgs
)

add_message_files(
  FILES
    ZadarCluster.msg
    ZadarClusters.msg
    ZadarTrack.msg
    ZadarTracks.msg
    ZadarOdometry.msg
)

generate_messages(
  DEPENDENCIES
    geometry_msgs
    sensor_msgs
    std_msgs
)

catkin_package(
  CATKIN_DEPENDS
    geometry_msgs
    message_runtime
    sensor_msgs
    std_msgs
)

install(DIRECTORY msg
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(FILES README.md
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
