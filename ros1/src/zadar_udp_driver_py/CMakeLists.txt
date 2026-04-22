cmake_minimum_required(VERSION 3.0.2)
project(zadar_udp_driver_py)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  rospy
  sensor_msgs
  std_msgs
  zadar_msgs
)

catkin_python_setup()

catkin_package(
  CATKIN_DEPENDS
    geometry_msgs
    rospy
    sensor_msgs
    std_msgs
    zadar_msgs
)

catkin_install_python(
  PROGRAMS
    scripts/zadar_udp_driver
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(FILES
  package.xml
  README.md
  setup.py
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
