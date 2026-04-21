#include "example_support.h"

#include <cstdint>

int main(int argc, char** argv) {
  using namespace zadar::webapi;
  using namespace zadar::webapi::examples;

  const std::string sensor_host = require_option(argc, argv, "--sensor-host");
  const std::string destination_ip = require_option(argc, argv, "--destination-ip");
  const int pcl_port = optional_int_option(argc, argv, "--pcl-port", 7777);
  const int imu_port = optional_int_option(argc, argv, "--imu-port", 36636);

  Client client(sensor_host);

  print_response(
      "Set Output Destination IP",
      client.set_output_destination_ip_address(destination_ip));
  print_response("Set PCL Port", client.set_pcl_port(pcl_port));
  print_response("Set IMU Port", client.set_imu_port(imu_port));
  print_response("Output Destination IP", client.get_output_destination_ip_address());
  print_response("PCL Port", client.get_pcl_port());
  print_response("IMU Port", client.get_imu_port());
  return 0;
}
