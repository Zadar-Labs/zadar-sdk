#include <iostream>

#include "example_support.h"
#include "zadar/udp/radar_listener.h"

int main(int argc, char** argv) {
  const auto options = zadar::udp::examples::parse_radar_options(
      argc,
      argv,
      "Receive Zadar UDP radar frames and print scan metadata plus sample points.",
      true,
      5);
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
      const auto& radar_scan = payload.frame.radar_scan();
      const auto& points = radar_scan.points();

      zadar::udp::examples::print_frame_banner(
          payload.frame_id,
          payload.timestamp.sec,
          payload.timestamp.nsec);
      std::cout
          << "Radar Scan: seq=" << radar_scan.header().seq()
          << ", stamp='" << zadar::udp::examples::format_timestamp_ns(radar_scan.header().stamp()) << "'"
          << ", frame_id='" << radar_scan.header().frame_id() << "'"
          << ", width=" << radar_scan.width()
          << ", height=" << radar_scan.height()
          << ", is_dense=" << radar_scan.is_dense() << '\n';

      std::cout << "Total Points: " << points.size() << '\n';
      const auto sample = zadar::udp::examples::sample_indices(
          static_cast<std::size_t>(points.size()),
          options.sample_count);
      for (std::size_t sample_index = 0; sample_index < sample.size(); ++sample_index) {
        const auto& point = points.Get(static_cast<int>(sample[sample_index]));
        std::cout
            << "  Pt" << (sample_index + 1)
            << ": x=" << point.x()
            << ", y=" << point.y()
            << ", z=" << point.z()
            << ", doppler=" << point.doppler()
            << ", snr=" << point.snr()
            << ", rcs=" << point.rcs() << '\n';
      }
      ++processed_frames;
    }
  } catch (const std::exception& error) {
    std::cerr << "Error: " << error.what() << '\n';
    return 1;
  }
}
