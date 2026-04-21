#include "zadar/udp/radar_listener.h"

#include <arpa/inet.h>
#include <cerrno>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <chrono>
#include <cstring>
#include <stdexcept>

namespace zadar::udp {

namespace {

std::runtime_error socket_error(const std::string& message) {
  return std::runtime_error(message + ": " + std::strerror(errno));
}

}  // namespace

RadarDataListener::RadarDataListener(
    std::string bind_address,
    std::uint16_t port,
    std::size_t receive_buffer_bytes,
    std::size_t max_buffered_frames,
    double frame_timeout_sec,
    std::optional<double> socket_timeout_sec)
    : bind_address_(std::move(bind_address)),
      port_(port),
      receive_buffer_bytes_(receive_buffer_bytes),
      frame_timeout_sec_(frame_timeout_sec),
      socket_timeout_sec_(socket_timeout_sec),
      reassembler_(max_buffered_frames) {
  if (frame_timeout_sec_ <= 0.0) {
    throw std::invalid_argument("frame_timeout_sec must be positive");
  }
}

RadarDataListener::~RadarDataListener() {
  close();
}

void RadarDataListener::open() {
  if (socket_fd_ != -1) {
    return;
  }

  socket_fd_ = ::socket(AF_INET, SOCK_DGRAM, 0);
  if (socket_fd_ < 0) {
    throw socket_error("Failed to create radar UDP socket");
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
    const auto error = socket_error("Failed to bind radar UDP socket");
    close();
    throw error;
  }
}

void RadarDataListener::close() {
  if (socket_fd_ != -1) {
    ::close(socket_fd_);
    socket_fd_ = -1;
  }
}

RadarListenerStats RadarDataListener::stats() const {
  return stats_;
}

std::optional<RadarDataOutput> RadarDataListener::read_frame() {
  open();
  while (true) {
    const auto datagram = recv_datagram();
    if (!datagram.has_value()) {
      return std::nullopt;
    }
    const double now_seconds = monotonic_seconds();
    ++stats_.packets_received;
    stats_.bytes_received += datagram->size();

    reassembler_.evict_stale_frames(now_seconds, frame_timeout_sec_);
    sync_reassembly_stats();

    std::optional<CompletedFrame> completed;
    try {
      completed = reassembler_.add_datagram(*datagram, now_seconds);
    } catch (const std::exception&) {
      ++stats_.malformed_packets;
      sync_reassembly_stats();
      return RadarDataOutput{RadarStatusCode::kImproperPacket, std::nullopt};
    }

    sync_reassembly_stats();
    if (!completed.has_value()) {
      continue;
    }

    zadar_pb::ZadarFrame radar_frame;
    if (!radar_frame.ParseFromArray(
            completed->payload.data(),
            static_cast<int>(completed->payload.size()))) {
      ++stats_.proto_parse_errors;
      return RadarDataOutput{
          RadarStatusCode::kProtoParsingError,
          std::nullopt,
      };
    }

    ++stats_.completed_frames;
    RadarDataPayload payload;
    payload.timestamp.sec = completed->header.timestamp_sec;
    payload.timestamp.nsec = completed->header.timestamp_nsec;
    payload.frame_id = completed->header.frame_id;
    payload.frame = std::move(radar_frame);
    return RadarDataOutput{RadarStatusCode::kFine, std::move(payload)};
  }
}

std::optional<std::vector<std::uint8_t>> RadarDataListener::recv_datagram() {
  std::vector<std::uint8_t> buffer(65535U);
  const ssize_t bytes_read =
      ::recvfrom(socket_fd_, buffer.data(), buffer.size(), 0, nullptr, nullptr);
  if (bytes_read < 0) {
    if (errno == EAGAIN || errno == EWOULDBLOCK) {
      return std::nullopt;
    }
    throw socket_error("Failed to receive radar UDP datagram");
  }
  buffer.resize(static_cast<std::size_t>(bytes_read));
  return buffer;
}

double RadarDataListener::monotonic_seconds() {
  const auto now = std::chrono::steady_clock::now().time_since_epoch();
  return std::chrono::duration_cast<std::chrono::duration<double>>(now).count();
}

void RadarDataListener::sync_reassembly_stats() {
  stats_.duplicate_fragments = reassembler_.duplicate_fragments();
  stats_.evicted_frames = reassembler_.evicted_frames();
}

}  // namespace zadar::udp
