#include "example_support.h"

#include <cstdint>

int main(int argc, char** argv) {
  using namespace zadar::webapi;
  using namespace zadar::webapi::examples;

  const std::string sensor_host = require_option(argc, argv, "--sensor-host");
  Client client(sensor_host);

  const std::string ptp_mode = optional_option(argc, argv, "--ptp-mode", "");
  const int sync_accuracy = optional_int_option(argc, argv, "--sync-accuracy", -1);
  const int trigger_offset = optional_int_option(argc, argv, "--trigger-offset", -1);

  if (!ptp_mode.empty()) {
    print_response("Set PTP Mode", client.set_ptp_mode(ptp_mode));
  }
  if (sync_accuracy >= 0) {
    print_response("Set PTP Sync Accuracy", client.set_ptp_sync_accuracy(sync_accuracy));
  }
  if (trigger_offset >= 0) {
    print_response("Set PTP Trigger Offset", client.set_ptp_trigger_offset(trigger_offset));
  }

  print_response("PTP Sync Status", client.get_ptp_sync_status());
  print_response("PTP Mode", client.get_ptp_mode());
  print_response("PTP Sync Accuracy", client.get_ptp_sync_accuracy());
  print_response("PTP Trigger Offset", client.get_ptp_trigger_offset());
  return 0;
}
