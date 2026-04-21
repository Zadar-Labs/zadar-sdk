#include "example_support.h"

#include <cstdint>

int main(int argc, char** argv) {
  using namespace zadar::webapi;
  using namespace zadar::webapi::examples;

  const std::string sensor_host = require_option(argc, argv, "--sensor-host");
  const bool stop = has_flag(argc, argv, "--stop");

  Client client(sensor_host);

  if (stop) {
    print_response("Stop Running Mode", client.stop_running_mode());
  } else {
    const int mode = optional_int_option(argc, argv, "--mode", -1);
    if (mode < 0) {
      std::cerr << "Missing required option: --mode\n";
      return 1;
    }
    print_response("Start Running Mode", client.set_running_mode(mode));
  }

  print_response("Running Mode", client.get_running_mode());
  return 0;
}
