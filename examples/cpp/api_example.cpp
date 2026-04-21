#include <cstdint>
#include <cstdlib>
#include <exception>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>

#include "zadar/udp/imu_listener.h"
#include "zadar/udp/radar_listener.h"
#include "zadar/webapi/client.h"
#include "zadar/webapi/driver_control.h"
#include "zadar_udp/example_support.h"
#include "zadar_webapi/example_support.h"

namespace {

struct Options {
  std::string sensor_host;
  std::string host_ip;
  std::string bind_address = "0.0.0.0";
  int pcl_port = 7777;
  int imu_port = 36636;
  std::optional<int> running_mode;
  std::size_t radar_frames = 3;
  std::size_t imu_packets = 3;
  double socket_timeout_sec = 5.0;
  std::optional<std::string> configured_device_ip;
  std::optional<std::string> ptp_mode;
  std::optional<int> ptp_sync_accuracy;
  std::optional<int> ptp_trigger_offset;
  bool stop_at_end = false;
};

void print_usage(const char* program_name) {
  std::cout
      << "End-to-end SDK example that configures sensor output over the Web API\n"
      << "and then receives radar and IMU data over UDP.\n\n"
      << "Usage: " << program_name << " --sensor-host <host> [options]\n\n"
      << "Options:\n"
      << "  --sensor-host <host>       Sensor hostname or IPv4 address. Required.\n"
      << "  --host-ip <ip>             Host IP address to program as the UDP destination.\n"
      << "  --bind-address <address>   Local interface for the UDP listeners. Default: 0.0.0.0\n"
      << "  --pcl-port <port>          Radar UDP port. Default: 7777\n"
      << "  --imu-port <port>          IMU UDP port. Default: 36636\n"
      << "  --running-mode <mode>      Running mode to start before reading UDP data.\n"
      << "  --radar-frames <count>     Number of completed radar frames to print. Default: 3\n"
      << "  --imu-packets <count>      Number of decoded IMU packets to print. Default: 3\n"
      << "  --socket-timeout-sec <s>   Timeout for each UDP read. Default: 5.0\n"
      << "  --set-device-ip <ip>       Optional static device IP override.\n"
      << "  --ptp-mode <mode>          Optional PTP mode update.\n"
      << "  --ptp-sync-accuracy <ns>   Optional PTP sync accuracy update.\n"
      << "  --ptp-trigger-offset <ns>  Optional PTP trigger offset update.\n"
      << "  --stop-at-end              Stop the running mode before exiting.\n"
      << "  --help                     Show this help message and exit.\n";
}

std::optional<std::string> find_option_value(
    int argc,
    char** argv,
    const std::string& option) {
  for (int i = 1; i + 1 < argc; ++i) {
    if (option == argv[i]) {
      return std::string(argv[i + 1]);
    }
  }
  return std::nullopt;
}

bool has_flag(int argc, char** argv, const std::string& option) {
  for (int i = 1; i < argc; ++i) {
    if (option == argv[i]) {
      return true;
    }
  }
  return false;
}

int parse_int_value(const std::string& value, const std::string& option_name) {
  try {
    return std::stoi(value);
  } catch (const std::exception&) {
    throw std::runtime_error("Invalid integer value for " + option_name + ": " + value);
  }
}

double parse_double_value(const std::string& value, const std::string& option_name) {
  try {
    return std::stod(value);
  } catch (const std::exception&) {
    throw std::runtime_error("Invalid floating-point value for " + option_name + ": " + value);
  }
}

Options parse_options(int argc, char** argv) {
  if (has_flag(argc, argv, "--help")) {
    print_usage(argv[0]);
    std::exit(0);
  }

  Options options;
  const auto sensor_host = find_option_value(argc, argv, "--sensor-host");
  if (!sensor_host.has_value() || sensor_host->empty()) {
    print_usage(argv[0]);
    throw std::runtime_error("--sensor-host is required.");
  }
  options.sensor_host = *sensor_host;

  if (const auto value = find_option_value(argc, argv, "--host-ip")) {
    options.host_ip = *value;
  }
  if (const auto value = find_option_value(argc, argv, "--bind-address")) {
    options.bind_address = *value;
  }
  if (const auto value = find_option_value(argc, argv, "--pcl-port")) {
    options.pcl_port = parse_int_value(*value, "--pcl-port");
  }
  if (const auto value = find_option_value(argc, argv, "--imu-port")) {
    options.imu_port = parse_int_value(*value, "--imu-port");
  }
  if (const auto value = find_option_value(argc, argv, "--running-mode")) {
    options.running_mode = parse_int_value(*value, "--running-mode");
  }
  if (const auto value = find_option_value(argc, argv, "--radar-frames")) {
    options.radar_frames = static_cast<std::size_t>(parse_int_value(*value, "--radar-frames"));
  }
  if (const auto value = find_option_value(argc, argv, "--imu-packets")) {
    options.imu_packets = static_cast<std::size_t>(parse_int_value(*value, "--imu-packets"));
  }
  if (const auto value = find_option_value(argc, argv, "--socket-timeout-sec")) {
    options.socket_timeout_sec = parse_double_value(*value, "--socket-timeout-sec");
  }
  if (const auto value = find_option_value(argc, argv, "--set-device-ip")) {
    options.configured_device_ip = *value;
  }
  if (const auto value = find_option_value(argc, argv, "--ptp-mode")) {
    options.ptp_mode = *value;
  }
  if (const auto value = find_option_value(argc, argv, "--ptp-sync-accuracy")) {
    options.ptp_sync_accuracy = parse_int_value(*value, "--ptp-sync-accuracy");
  }
  if (const auto value = find_option_value(argc, argv, "--ptp-trigger-offset")) {
    options.ptp_trigger_offset = parse_int_value(*value, "--ptp-trigger-offset");
  }
  options.stop_at_end = has_flag(argc, argv, "--stop-at-end");

  return options;
}

zadar::udp::RadarDataPayload read_next_radar_frame(zadar::udp::RadarDataListener& listener) {
  while (true) {
    const auto output = listener.read_frame();
    if (!output.has_value()) {
      throw std::runtime_error("Timed out waiting for a radar frame.");
    }
    if (output->status_code == zadar::udp::RadarStatusCode::kFine && output->data.has_value()) {
      return *output->data;
    }
    std::cout << "Skipping radar frame with status_code="
              << static_cast<int>(output->status_code) << '\n';
  }
}

zadar::udp::ImuDataPayload read_next_imu_packet(zadar::udp::ImuDataListener& listener) {
  while (true) {
    const auto output = listener.read_packet();
    if (!output.has_value()) {
      throw std::runtime_error("Timed out waiting for an IMU packet.");
    }
    if (output->status_code == zadar::udp::ImuStatusCode::kFine && output->data.has_value()) {
      return *output->data;
    }
    std::cout << "Skipping IMU packet with status_code="
              << static_cast<int>(output->status_code) << '\n';
  }
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const Options options = parse_options(argc, argv);
    const auto settings = zadar::webapi::resolve_managed_network_settings(
        options.sensor_host,
        options.host_ip,
        options.bind_address,
        "");

    std::cout << "Resolved network settings:\n";
    std::cout << "  destination_ip=" << settings.destination_ip << '\n';
    std::cout << "  bind_address=" << settings.bind_address << '\n';
    std::cout << "  pcl_port=" << options.pcl_port << '\n';
    std::cout << "  imu_port=" << options.imu_port << '\n';

    zadar::webapi::Client client(options.sensor_host);
    zadar::udp::RadarDataListener radar_listener(
        settings.bind_address,
        static_cast<std::uint16_t>(options.pcl_port),
        zadar::udp::RadarDataListener::kDefaultReceiveBufferBytes,
        zadar::udp::RadarDataListener::kDefaultMaxBufferedFrames,
        zadar::udp::RadarDataListener::kDefaultFrameTimeoutSec,
        std::optional<double>(options.socket_timeout_sec));
    zadar::udp::ImuDataListener imu_listener(
        settings.bind_address,
        static_cast<std::uint16_t>(options.imu_port),
        zadar::udp::ImuDataListener::kDefaultReceiveBufferBytes,
        std::optional<double>(options.socket_timeout_sec));

    std::cout << "\nOpening UDP listeners...\n";
    radar_listener.open();
    imu_listener.open();

    zadar::webapi::examples::print_response("Sensor Info", client.get_sensor_info());
    zadar::webapi::examples::print_response("Device Modes", client.get_device_modes());
    zadar::webapi::examples::print_response("Running Mode", client.get_running_mode());
    zadar::webapi::examples::print_response(
        "Configured Device IP",
        client.get_configured_device_ip_address());
    zadar::webapi::examples::print_response(
        "Current Device IP",
        client.get_current_device_ip_address());
    zadar::webapi::examples::print_response(
        "Output Destination IP",
        client.get_output_destination_ip_address());
    zadar::webapi::examples::print_response("Configured PCL Port", client.get_pcl_port());
    zadar::webapi::examples::print_response("Configured IMU Port", client.get_imu_port());
    zadar::webapi::examples::print_response("Startup Mode", client.get_startup_mode());
    zadar::webapi::examples::print_response("PTP Sync Status", client.get_ptp_sync_status());
    zadar::webapi::examples::print_response("PTP Mode", client.get_ptp_mode());
    zadar::webapi::examples::print_response(
        "PTP Sync Accuracy",
        client.get_ptp_sync_accuracy());
    zadar::webapi::examples::print_response(
        "PTP Trigger Offset",
        client.get_ptp_trigger_offset());

    if (options.configured_device_ip.has_value()) {
      const auto response =
          client.set_configured_device_ip_address_static(*options.configured_device_ip);
      zadar::webapi::examples::print_response("Set Configured Device IP", response);
      zadar::webapi::require_success("Setting configured device IP", response);
    }

    if (options.ptp_mode.has_value()) {
      const auto response = client.set_ptp_mode(*options.ptp_mode);
      zadar::webapi::examples::print_response("Set PTP Mode", response);
      zadar::webapi::require_success("Setting PTP mode", response);
    }

    if (options.ptp_sync_accuracy.has_value()) {
      const auto response = client.set_ptp_sync_accuracy(*options.ptp_sync_accuracy);
      zadar::webapi::examples::print_response("Set PTP Sync Accuracy", response);
      zadar::webapi::require_success("Setting PTP sync accuracy", response);
    }

    if (options.ptp_trigger_offset.has_value()) {
      const auto response = client.set_ptp_trigger_offset(*options.ptp_trigger_offset);
      zadar::webapi::examples::print_response("Set PTP Trigger Offset", response);
      zadar::webapi::require_success("Setting PTP trigger offset", response);
    }

    std::cout << "\nConfiguring output destination and UDP ports...\n";
    {
      const auto response = client.set_output_destination_ip_address(settings.destination_ip);
      zadar::webapi::examples::print_response("Set Output Destination IP", response);
      zadar::webapi::require_success("Configuring output destination IP", response);
    }
    {
      const auto response = client.set_pcl_port(options.pcl_port);
      zadar::webapi::examples::print_response("Set PCL Port", response);
      zadar::webapi::require_success("Configuring radar data port", response);
    }
    {
      const auto response = client.set_imu_port(options.imu_port);
      zadar::webapi::examples::print_response("Set IMU Port", response);
      zadar::webapi::require_success("Configuring IMU port", response);
    }

    if (options.running_mode.has_value()) {
      const auto response = client.set_running_mode(*options.running_mode);
      zadar::webapi::examples::print_response(
          "Start Running Mode " + std::to_string(*options.running_mode),
          response);
      zadar::webapi::require_success(
          "Starting running mode " + std::to_string(*options.running_mode),
          response);
    } else {
      std::cout
          << "\nNo --running-mode was provided. The example will expect the sensor\n"
          << "to already be streaming.\n";
    }

    zadar::webapi::examples::print_response(
        "Verified Output Destination IP",
        client.get_output_destination_ip_address());
    zadar::webapi::examples::print_response("Verified PCL Port", client.get_pcl_port());
    zadar::webapi::examples::print_response("Verified IMU Port", client.get_imu_port());
    zadar::webapi::examples::print_response("Verified Running Mode", client.get_running_mode());

    std::cout << "\nReading radar frames...\n";
    for (std::size_t i = 0; i < options.radar_frames; ++i) {
      const auto payload = read_next_radar_frame(radar_listener);
      std::cout << "\n=== Radar Frame #" << payload.frame_id << " ===\n";
      std::cout << "Timestamp: "
                << zadar::udp::examples::format_timestamp(
                       payload.timestamp.sec,
                       payload.timestamp.nsec)
                << '\n';
      std::cout << "Points: " << payload.frame.radar_scan().points_size() << '\n';
      std::cout << "Clusters: " << payload.frame.clusters_size() << '\n';
      std::cout << "Tracks: " << payload.frame.tracks_size() << '\n';
      std::cout << "Odometry Present: "
                << (payload.frame.has_odometry() ? "true" : "false") << '\n';
    }

    std::cout << "\nReading IMU packets...\n";
    for (std::size_t i = 0; i < options.imu_packets; ++i) {
      const auto payload = read_next_imu_packet(imu_listener);
      std::cout << "\n=== IMU Packet #" << payload.frame_id << " ===\n";
      std::cout << "Timestamp: "
                << zadar::udp::examples::format_timestamp(
                       payload.timestamp.sec,
                       payload.timestamp.nsec)
                << '\n';
      std::cout << "Accel: " << payload.packet.acceleration_x << ", "
                << payload.packet.acceleration_y << ", "
                << payload.packet.acceleration_z << '\n';
      std::cout << "Gyro:  " << payload.packet.angular_rate_x << ", "
                << payload.packet.angular_rate_y << ", "
                << payload.packet.angular_rate_z << '\n';
    }

    if (options.stop_at_end) {
      const auto response = client.stop_running_mode();
      zadar::webapi::examples::print_response("Stop Running Mode", response);
      zadar::webapi::require_success("Stopping running mode", response);
    }
  } catch (const std::exception& error) {
    std::cerr << "Error: " << error.what() << '\n';
    return 1;
  }

  return 0;
}
