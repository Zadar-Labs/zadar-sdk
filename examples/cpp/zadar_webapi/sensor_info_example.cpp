#include "example_support.h"

int main(int argc, char** argv) {
  using namespace zadar::webapi;
  using namespace zadar::webapi::examples;

  const std::string sensor_host = require_option(argc, argv, "--sensor-host");
  Client client(sensor_host);

  print_response("Heartbeat", client.heartbeat());
  print_response("Sensor Info", client.get_sensor_info());
  print_response("Device Modes", client.get_device_modes());
  print_response("Running Mode", client.get_running_mode());
  return 0;
}
