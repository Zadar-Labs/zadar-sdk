#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

namespace zadar::udp {

struct FramePacketHeader {
  std::uint16_t radar_id = 0;
  std::uint16_t data_format = 0;
  std::uint32_t points_in_frame = 0;
  std::uint64_t timestamp_sec = 0;
  std::uint64_t timestamp_nsec = 0;
  std::uint16_t frame_id = 0;
  std::uint16_t packets_in_frame = 0;
  std::uint16_t packet_index = 0;
  std::uint16_t data_size = 0;

  static constexpr std::size_t kHeaderSize = 32;

  [[nodiscard]] std::uint64_t timestamp_ns() const {
    return (timestamp_sec * 1000000000ULL) + timestamp_nsec;
  }
};

struct FramePacket {
  FramePacketHeader header;
  std::vector<std::uint8_t> fragment;
};

namespace detail {

template <typename T>
T read_le(const std::uint8_t* data, std::size_t offset) {
  T value{};
  std::memcpy(&value, data + offset, sizeof(T));
  return value;
}

}  // namespace detail

inline FramePacket parse_frame_packet(const std::vector<std::uint8_t>& datagram) {
  if (datagram.size() < FramePacketHeader::kHeaderSize) {
    throw std::runtime_error(
        "Datagram is too small for a Zadar UDP header: expected at least " +
        std::to_string(FramePacketHeader::kHeaderSize) + " bytes");
  }

  const auto* data = datagram.data();
  FramePacket packet;
  packet.header.radar_id = detail::read_le<std::uint16_t>(data, 0);
  packet.header.data_format = detail::read_le<std::uint16_t>(data, 2);
  packet.header.points_in_frame = detail::read_le<std::uint32_t>(data, 4);
  packet.header.timestamp_sec = detail::read_le<std::uint64_t>(data, 8);
  packet.header.timestamp_nsec = detail::read_le<std::uint64_t>(data, 16);
  packet.header.frame_id = detail::read_le<std::uint16_t>(data, 24);
  packet.header.packets_in_frame = detail::read_le<std::uint16_t>(data, 26);
  packet.header.packet_index = detail::read_le<std::uint16_t>(data, 28);
  packet.header.data_size = detail::read_le<std::uint16_t>(data, 30);

  const std::size_t fragment_end =
      FramePacketHeader::kHeaderSize + packet.header.data_size;
  if (datagram.size() < fragment_end) {
    throw std::runtime_error(
        "Datagram payload is truncated: expected " +
        std::to_string(fragment_end) + " bytes");
  }

  packet.fragment.assign(
      datagram.begin() + static_cast<std::ptrdiff_t>(FramePacketHeader::kHeaderSize),
      datagram.begin() + static_cast<std::ptrdiff_t>(fragment_end));
  return packet;
}

}  // namespace zadar::udp
