#include <iostream>

#include "example_support.h"
#include "zadar/udp/imu_listener.h"

int main(int argc, char** argv) {
  const auto options = zadar::udp::examples::parse_imu_options(
      argc,
      argv,
      "Receive Zadar UDP IMU packets and print acceleration and gyro data.");
  zadar::udp::ImuDataListener listener(options.bind_address, options.port);

  try {
    std::size_t processed_packets = 0;
    while (!zadar::udp::examples::should_stop(processed_packets, options.packet_limit)) {
      const auto out = listener.read_packet();
      if (!out.has_value()) {
        continue;
      }
      if (out->status_code != zadar::udp::ImuStatusCode::kFine || !out->data) {
        std::cout << "Warning: Status code indicates an issue with the IMU data\n";
        continue;
      }

      const auto& payload = *out->data;
      const auto& packet = payload.packet;
      std::cout << "\nIMU Packet #" << processed_packets << '\n';
      std::cout << "Sensor Frame ID: " << payload.frame_id << '\n';
      std::cout
          << "Timestamp: "
          << zadar::udp::examples::format_timestamp(
                 payload.timestamp.sec,
                 payload.timestamp.nsec)
          << '\n';
      std::cout
          << "Accel: " << packet.acceleration_x
          << ", " << packet.acceleration_y
          << ", " << packet.acceleration_z << '\n';
      std::cout
          << "Gyro:  " << packet.angular_rate_x
          << ", " << packet.angular_rate_y
          << ", " << packet.angular_rate_z << '\n';
      ++processed_packets;
    }
  } catch (const std::exception& error) {
    std::cerr << "Error: " << error.what() << '\n';
    return 1;
  }
}
