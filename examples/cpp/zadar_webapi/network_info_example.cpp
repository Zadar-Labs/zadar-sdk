#include "example_support.h"

#include <cstdint>

int main(int argc, char** argv) {
  using namespace zadar::webapi;
  using namespace zadar::webapi::examples;

  const std::string sensor_host = require_option(argc, argv, "--sensor-host");
  Client client(sensor_host);

  print_response("Configured Device IP", client.get_configured_device_ip_address());
  print_response("Current Device IP", client.get_current_device_ip_address());
  print_response("Output Destination IP", client.get_output_destination_ip_address());
  print_response("PCL Port", client.get_pcl_port());
  print_response("IMU Port", client.get_imu_port());
  return 0;
}
