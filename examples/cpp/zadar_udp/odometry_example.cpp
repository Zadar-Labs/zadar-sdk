#include <iostream>

#include "example_support.h"
#include "zadar/udp/radar_listener.h"

int main(int argc, char** argv) {
  const auto options = zadar::udp::examples::parse_radar_options(
      argc,
      argv,
      "Receive Zadar UDP radar frames and print odometry data when present.");
  zadar::udp::RadarDataListener listener(options.bind_address, options.port);

  try {
    std::size_t processed_frames = 0;
    while (!zadar::udp::examples::should_stop(processed_frames, options.frame_limit)) {
      const auto out = listener.read_frame();
      if (!out.has_value()) {
        continue;
      }
      if (out->status_code != zadar::udp::RadarStatusCode::kFine || !out->data) {
        std::cout << "Warning: Status code indicates an issue with the radar data\n";
        continue;
      }

      const auto& payload = *out->data;
      zadar::udp::examples::print_frame_banner(
          payload.frame_id,
          payload.timestamp.sec,
          payload.timestamp.nsec);

      if (!payload.frame.has_odometry()) {
        std::cout << "Odometry: not present in this frame\n";
        continue;
      }

      const auto& odometry = payload.frame.odometry();
      std::cout
          << "Odometry: frame=" << odometry.frame_num()
          << ", stamp='" << zadar::udp::examples::format_timestamp_ns(odometry.stamp()) << "'"
          << ", euler=(" << odometry.phi() << ", " << odometry.psi() << ", " << odometry.theta() << ")"
          << ", vel=(" << odometry.vx() << ", " << odometry.vy() << ", " << odometry.vz() << ")"
          << ", raw_vel=(" << odometry.raw_vx() << ", " << odometry.raw_vy() << ", " << odometry.raw_vz() << ")"
          << ", omega=(" << odometry.omega_x() << ", " << odometry.omega_y() << ", " << odometry.omega_z() << ")\n";
      ++processed_frames;
    }
  } catch (const std::exception& error) {
    std::cerr << "Error: " << error.what() << '\n';
    return 1;
  }
}
