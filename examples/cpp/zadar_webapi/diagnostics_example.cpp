#include "example_support.h"

#include <cstdint>

int main(int argc, char** argv) {
  using namespace zadar::webapi;
  using namespace zadar::webapi::examples;

  const std::string sensor_host = require_option(argc, argv, "--sensor-host");
  const int timeout_ms = optional_int_option(argc, argv, "--timeout-ms", 10000);

  Client client(sensor_host);
  print_response("Diagnostics", client.get_diagnostics(timeout_ms));
  return 0;
}
