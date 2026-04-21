#include "example_support.h"

#include <cstdint>
#include <iostream>

int main(int argc, char** argv) {
  using namespace zadar::webapi;
  using namespace zadar::webapi::examples;

  const std::string sensor_host = require_option(argc, argv, "--sensor-host");
  const bool reset = has_flag(argc, argv, "--reset");

  if (reset && has_flag(argc, argv, "--mode")) {
    std::cerr << "--mode and --reset cannot be used together\n";
    return 1;
  }

  Client client(sensor_host);

  if (reset) {
    print_response("Reset Startup Mode", client.reset_startup_mode());
  } else {
    const int mode = optional_int_option(argc, argv, "--mode", -1);
    if (mode >= 0) {
      print_response("Set Startup Mode", client.set_startup_mode(mode));
    }
  }

  print_response("Startup Mode", client.get_startup_mode());
  return 0;
}
