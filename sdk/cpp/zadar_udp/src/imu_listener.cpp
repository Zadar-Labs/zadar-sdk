#include "zadar/udp/imu_listener.h"

#include <arpa/inet.h>
#include <cerrno>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cstring>
#include <stdexcept>

#include "zadar/udp/crc64.h"

namespace zadar::udp {

namespace {

constexpr std::size_t kHeaderSize = 48U;
constexpr std::size_t kDataSize = 56U;
constexpr std::size_t kPacketSize = kHeaderSize + kDataSize;

template <typename T>
T read_le(const std::uint8_t* data, std::size_t offset) {
  T value{};
  std::memcpy(&value, data + offset, sizeof(T));
  return value;
}

std::runtime_error socket_error(const std::string& message) {
  return std::runtime_error(message + ": " + std::strerror(errno));
}

}  // namespace

ImuDataListener::ImuDataListener(
    std::string bind_address,
    std::uint16_t port,
    std::size_t receive_buffer_bytes,
    std::optional<double> socket_timeout_sec)
    : bind_address_(std::move(bind_address)),
      port_(port),
      receive_buffer_bytes_(receive_buffer_bytes),
      socket_timeout_sec_(socket_timeout_sec) {}

ImuDataListener::~ImuDataListener() {
  close();
}

void ImuDataListener::open() {
  if (socket_fd_ != -1) {
    return;
  }

  socket_fd_ = ::socket(AF_INET, SOCK_DGRAM, 0);
  if (socket_fd_ < 0) {
    throw socket_error("Failed to create IMU UDP socket");
  }

  const int buffer_bytes = static_cast<int>(receive_buffer_bytes_);
  ::setsockopt(
      socket_fd_,
      SOL_SOCKET,
      SO_RCVBUF,
      &buffer_bytes,
      sizeof(buffer_bytes));
  if (socket_timeout_sec_.has_value()) {
    const auto timeout_sec = *socket_timeout_sec_;
    if (timeout_sec < 0.0) {
      close();
      throw std::invalid_argument("socket_timeout_sec must be non-negative");
    }
    timeval timeout{};
    timeout.tv_sec = static_cast<time_t>(timeout_sec);
    timeout.tv_usec = static_cast<suseconds_t>(
        (timeout_sec - static_cast<double>(timeout.tv_sec)) * 1000000.0);
    ::setsockopt(socket_fd_, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
  }

  sockaddr_in address{};
  address.sin_family = AF_INET;
  address.sin_port = htons(port_);
  address.sin_addr.s_addr =
      bind_address_ == "0.0.0.0" ? INADDR_ANY : inet_addr(bind_address_.c_str());

  if (::bind(
          socket_fd_,
          reinterpret_cast<const sockaddr*>(&address),
          sizeof(address)) < 0) {
    const auto error = socket_error("Failed to bind IMU UDP socket");
    close();
    throw error;
  }

}

void ImuDataListener::close() {
  if (socket_fd_ != -1) {
    ::close(socket_fd_);
    socket_fd_ = -1;
  }
}

ImuListenerStats ImuDataListener::stats() const {
  return stats_;
}

std::optional<ImuDataOutput> ImuDataListener::read_packet() {
  open();

  const auto datagram = recv_datagram();
  if (!datagram.has_value()) {
    return std::nullopt;
  }
  ++stats_.packets_received;
  stats_.bytes_received += datagram->size();

  if (datagram->size() < kPacketSize) {
    ++stats_.malformed_packets;
    return ImuDataOutput{ImuStatusCode::kImproperPacket, std::nullopt};
  }

  const auto* data = datagram->data();
  const std::uint64_t packet_crc =
      read_le<std::uint64_t>(data, datagram->size() - sizeof(std::uint64_t));
  CRC64Ecma182 crc;
  crc.update(data, datagram->size() - sizeof(std::uint64_t));
  if (packet_crc != crc.digest()) {
    ++stats_.crc_errors;
    return ImuDataOutput{ImuStatusCode::kImproperCrc, std::nullopt};
  }

  const std::uint32_t frame_id = read_le<std::uint32_t>(data, 16);
  const std::uint32_t data_size = read_le<std::uint32_t>(data, 20);
  const std::uint64_t timestamp_sec = read_le<std::uint64_t>(data, 32);
  const std::uint64_t timestamp_nsec = read_le<std::uint64_t>(data, 40);
  static_cast<void>(data_size);

  const std::uint64_t diagnostic_timestamp = read_le<std::uint64_t>(data, 48);
  const std::uint64_t accelerometer_timestamp = read_le<std::uint64_t>(data, 56);
  const std::uint64_t gyroscope_timestamp = read_le<std::uint64_t>(data, 64);
  const float acceleration_x = read_le<float>(data, 72);
  const float acceleration_y = read_le<float>(data, 76);
  const float acceleration_z = read_le<float>(data, 80);
  const float angular_rate_x = read_le<float>(data, 84);
  const float angular_rate_y = read_le<float>(data, 88);
  const float angular_rate_z = read_le<float>(data, 92);
  const std::uint64_t embedded_crc = read_le<std::uint64_t>(data, 96);

  if (embedded_crc != packet_crc) {
    ++stats_.crc_errors;
    return ImuDataOutput{ImuStatusCode::kImproperCrc, std::nullopt};
  }

  ++stats_.completed_packets;
  ImuDataPayload payload;
  payload.timestamp.sec = timestamp_sec;
  payload.timestamp.nsec = timestamp_nsec;
  payload.frame_id = frame_id;
  payload.packet = {
      diagnostic_timestamp,
      accelerometer_timestamp,
      gyroscope_timestamp,
      acceleration_x,
      acceleration_y,
      acceleration_z,
      angular_rate_x,
      angular_rate_y,
      angular_rate_z,
  };
  return ImuDataOutput{ImuStatusCode::kFine, payload};
}

std::optional<std::vector<std::uint8_t>> ImuDataListener::recv_datagram() {
  std::vector<std::uint8_t> buffer(65535U);
  const ssize_t bytes_read =
      ::recvfrom(socket_fd_, buffer.data(), buffer.size(), 0, nullptr, nullptr);
  if (bytes_read < 0) {
    if (errno == EAGAIN || errno == EWOULDBLOCK) {
      return std::nullopt;
    }
    throw socket_error("Failed to receive IMU UDP datagram");
  }
  buffer.resize(static_cast<std::size_t>(bytes_read));
  return buffer;
}

}  // namespace zadar::udp
