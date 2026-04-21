#include <iostream>

#include "example_support.h"
#include "zadar/udp/radar_listener.h"

int main(int argc, char** argv) {
  const auto options = zadar::udp::examples::parse_radar_options(
      argc,
      argv,
      "Receive Zadar UDP radar frames and print sample cluster data.",
      true,
      3);
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
      const auto& clusters = payload.frame.clusters();
      zadar::udp::examples::print_frame_banner(
          payload.frame_id,
          payload.timestamp.sec,
          payload.timestamp.nsec);
      std::cout << "Total Clusters: " << clusters.size() << '\n';

      const auto sample = zadar::udp::examples::sample_indices(
          static_cast<std::size_t>(clusters.size()),
          options.sample_count);
      for (std::size_t sample_index = 0; sample_index < sample.size(); ++sample_index) {
        const auto& cluster = clusters.Get(static_cast<int>(sample[sample_index]));
        std::cout
            << "  Cluster" << (sample_index + 1)
            << ": id=" << cluster.cluster_id()
            << ", pos=(" << cluster.x() << ", " << cluster.y() << ", " << cluster.z() << ")"
            << ", doppler=" << cluster.doppler()
            << ", points=" << cluster.num_points()
            << ", static=" << cluster.is_static()
            << ", vertices=" << cluster.vertices_size() << '\n';
      }
      ++processed_frames;
    }
  } catch (const std::exception& error) {
    std::cerr << "Error: " << error.what() << '\n';
    return 1;
  }
}
