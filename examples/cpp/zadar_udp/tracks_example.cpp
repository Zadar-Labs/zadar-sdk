#include <iostream>

#include "example_support.h"
#include "zadar/udp/radar_listener.h"

int main(int argc, char** argv) {
  const auto options = zadar::udp::examples::parse_radar_options(
      argc,
      argv,
      "Receive Zadar UDP radar frames and print sample track data.",
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
      const auto& tracks = payload.frame.tracks();
      zadar::udp::examples::print_frame_banner(
          payload.frame_id,
          payload.timestamp.sec,
          payload.timestamp.nsec);
      std::cout << "Total Tracks: " << tracks.size() << '\n';

      const auto sample = zadar::udp::examples::sample_indices(
          static_cast<std::size_t>(tracks.size()),
          options.sample_count);
      for (std::size_t sample_index = 0; sample_index < sample.size(); ++sample_index) {
        const auto& track = tracks.Get(static_cast<int>(sample[sample_index]));
        std::cout
            << "  Track" << (sample_index + 1)
            << ": id=" << track.track_id()
            << ", pos=(" << track.x() << ", " << track.y() << ", " << track.z() << ")"
            << ", vel=(" << track.vx() << ", " << track.vy() << ", " << track.vz() << ")"
            << ", speed=" << track.speed()
            << ", state=" << track.state()
            << ", cluster=" << track.latest_cluster_id()
            << ", points=" << track.num_points() << '\n';
      }
      ++processed_frames;
    }
  } catch (const std::exception& error) {
    std::cerr << "Error: " << error.what() << '\n';
    return 1;
  }
}
