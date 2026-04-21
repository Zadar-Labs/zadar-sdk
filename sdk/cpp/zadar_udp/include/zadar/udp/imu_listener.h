#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace zadar::udp {

enum class ImuStatusCode {
  kImproperPacket = -1,
  kImproperCrc = -2,
  kFine = 0,
};

struct ImuPacketData {
  std::uint64_t diagnostic_timestamp = 0;
  std::uint64_t accelerometer_timestamp = 0;
  std::uint64_t gyroscope_timestamp = 0;
  float acceleration_x = 0.0F;
  float acceleration_y = 0.0F;
  float acceleration_z = 0.0F;
  float angular_rate_x = 0.0F;
  float angular_rate_y = 0.0F;
  float angular_rate_z = 0.0F;
};

struct ImuTimestamp {
  std::uint64_t sec = 0;
  std::uint64_t nsec = 0;
};

struct ImuDataPayload {
  ImuTimestamp timestamp;
  std::uint32_t frame_id = 0;
  ImuPacketData packet;
};

struct ImuDataOutput {
  ImuStatusCode status_code = ImuStatusCode::kImproperPacket;
  std::optional<ImuDataPayload> data;
};

struct ImuListenerStats {
  std::size_t packets_received = 0;
  std::size_t bytes_received = 0;
  std::size_t malformed_packets = 0;
  std::size_t crc_errors = 0;
  std::size_t completed_packets = 0;
};

class ImuDataListener {
 public:
  static constexpr std::size_t kDefaultReceiveBufferBytes = 4U * 1024U * 1024U;

  ImuDataListener(
      std::string bind_address = "0.0.0.0",
      std::uint16_t port = 36636,
      std::size_t receive_buffer_bytes = kDefaultReceiveBufferBytes,
      std::optional<double> socket_timeout_sec = std::nullopt);

  ~ImuDataListener();

  void open();
  void close();
  [[nodiscard]] ImuListenerStats stats() const;
  [[nodiscard]] std::optional<ImuDataOutput> read_packet();

 private:
  [[nodiscard]] std::optional<std::vector<std::uint8_t>> recv_datagram();

  std::string bind_address_;
  std::uint16_t port_;
  std::size_t receive_buffer_bytes_;
  std::optional<double> socket_timeout_sec_;
  int socket_fd_ = -1;
  ImuListenerStats stats_;
};

}  // namespace zadar::udp
