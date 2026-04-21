#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "ZadarFrame.pb.h"
#include "zadar/udp/frame_reassembler.h"

namespace zadar::udp {

enum class RadarStatusCode {
  kImproperPacket = -1,
  kImproperCrc = -2,
  kFine = 0,
  kProtoParsingError = 1,
};

struct Timestamp {
  std::uint64_t sec = 0;
  std::uint64_t nsec = 0;
};

struct RadarDataPayload {
  Timestamp timestamp;
  std::uint16_t frame_id = 0;
  zadar_pb::ZadarFrame frame;
};

struct RadarDataOutput {
  RadarStatusCode status_code = RadarStatusCode::kImproperPacket;
  std::optional<RadarDataPayload> data;
};

struct RadarListenerStats {
  std::size_t packets_received = 0;
  std::size_t bytes_received = 0;
  std::size_t malformed_packets = 0;
  std::size_t duplicate_fragments = 0;
  std::size_t completed_frames = 0;
  std::size_t proto_parse_errors = 0;
  std::size_t evicted_frames = 0;
};

class RadarDataListener {
 public:
  static constexpr std::size_t kDefaultReceiveBufferBytes = 64U * 1024U * 1024U;
  static constexpr std::size_t kDefaultMaxBufferedFrames = 128U;
  static constexpr double kDefaultFrameTimeoutSec = 1.0;

  RadarDataListener(
      std::string bind_address = "0.0.0.0",
      std::uint16_t port = 7777,
      std::size_t receive_buffer_bytes = kDefaultReceiveBufferBytes,
      std::size_t max_buffered_frames = kDefaultMaxBufferedFrames,
      double frame_timeout_sec = kDefaultFrameTimeoutSec,
      std::optional<double> socket_timeout_sec = std::nullopt);

  ~RadarDataListener();

  void open();
  void close();
  [[nodiscard]] RadarListenerStats stats() const;
  [[nodiscard]] std::optional<RadarDataOutput> read_frame();

 private:
  [[nodiscard]] std::optional<std::vector<std::uint8_t>> recv_datagram();
  static double monotonic_seconds();
  void sync_reassembly_stats();

  std::string bind_address_;
  std::uint16_t port_;
  std::size_t receive_buffer_bytes_;
  double frame_timeout_sec_;
  std::optional<double> socket_timeout_sec_;
  int socket_fd_ = -1;
  FrameReassembler reassembler_;
  RadarListenerStats stats_;
};

}  // namespace zadar::udp
