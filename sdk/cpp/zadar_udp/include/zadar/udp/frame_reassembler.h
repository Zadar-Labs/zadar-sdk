#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <map>
#include <optional>
#include <stdexcept>
#include <vector>

#include "zadar/udp/frame_packet.h"

namespace zadar::udp {

struct CompletedFrame {
  FramePacketHeader header;
  std::vector<std::uint8_t> payload;
};

class FrameReassembler {
 public:
  explicit FrameReassembler(std::size_t max_inflight_frames = 32)
      : max_inflight_frames_(max_inflight_frames) {
    if (max_inflight_frames_ == 0) {
      throw std::invalid_argument("max_inflight_frames must be at least 1");
    }
  }

  [[nodiscard]] std::size_t inflight_count() const { return frames_.size(); }
  [[nodiscard]] std::size_t duplicate_fragments() const {
    return duplicate_fragments_;
  }
  [[nodiscard]] std::size_t evicted_frames() const { return evicted_frames_; }

  void clear() { frames_.clear(); }

  std::optional<CompletedFrame> add_datagram(
      const std::vector<std::uint8_t>& datagram,
      double now_seconds) {
    return add_packet(parse_frame_packet(datagram), now_seconds);
  }

  std::size_t evict_stale_frames(double now_seconds, double timeout_sec) {
    if (timeout_sec <= 0.0) {
      throw std::invalid_argument("timeout_sec must be positive");
    }

    std::vector<std::uint16_t> stale_frame_ids;
    for (const auto& [frame_id, frame] : frames_) {
      if ((now_seconds - frame.last_updated) > timeout_sec) {
        stale_frame_ids.push_back(frame_id);
      }
    }

    for (const auto frame_id : stale_frame_ids) {
      frames_.erase(frame_id);
    }
    evicted_frames_ += stale_frame_ids.size();
    return stale_frame_ids.size();
  }

 private:
  struct InFlightFrame {
    FramePacketHeader header;
    std::vector<std::vector<std::uint8_t>> fragments;
    std::vector<bool> received;
    std::size_t received_count = 0;
    double created_at = 0.0;
    double last_updated = 0.0;
  };

  std::optional<CompletedFrame> add_packet(
      const FramePacket& packet,
      double now_seconds) {
    const auto& header = packet.header;
    if (header.packets_in_frame == 0) {
      throw std::runtime_error("packets_in_frame must be at least 1");
    }
    if (header.packet_index >= header.packets_in_frame) {
      throw std::runtime_error("packet_index is out of range");
    }

    const bool frame_exists = frames_.find(header.frame_id) != frames_.end();
    if (!frame_exists) {
      trim_oldest_frames_before_insert();
    }

    auto [it, inserted] = frames_.try_emplace(header.frame_id);
    auto& in_flight = it->second;
    if (inserted) {
      in_flight.header = header;
      in_flight.fragments.resize(header.packets_in_frame);
      in_flight.received.assign(header.packets_in_frame, false);
      in_flight.created_at = now_seconds;
      in_flight.last_updated = now_seconds;
    } else {
      validate_compatible_header(in_flight.header, header);
      in_flight.last_updated = now_seconds;
    }

    if (!in_flight.received[header.packet_index]) {
      in_flight.fragments[header.packet_index] = packet.fragment;
      in_flight.received[header.packet_index] = true;
      ++in_flight.received_count;
    } else if (in_flight.fragments[header.packet_index] != packet.fragment) {
      throw std::runtime_error("conflicting duplicate fragment");
    } else {
      ++duplicate_fragments_;
      return std::nullopt;
    }

    if (in_flight.received_count != header.packets_in_frame) {
      return std::nullopt;
    }

    CompletedFrame completed;
    completed.header = in_flight.header;
    std::size_t payload_size = 0;
    for (const auto& fragment : in_flight.fragments) {
      payload_size += fragment.size();
    }
    completed.payload.reserve(payload_size);
    for (const auto& fragment : in_flight.fragments) {
      completed.payload.insert(
          completed.payload.end(),
          fragment.begin(),
          fragment.end());
    }

    frames_.erase(header.frame_id);
    return completed;
  }

  void trim_oldest_frames_before_insert() {
    while (frames_.size() >= max_inflight_frames_) {
      const auto oldest_it = std::min_element(
          frames_.begin(),
          frames_.end(),
          [](const auto& lhs, const auto& rhs) {
            return lhs.second.last_updated < rhs.second.last_updated;
          });
      frames_.erase(oldest_it);
      ++evicted_frames_;
    }
  }

  static void validate_compatible_header(
      const FramePacketHeader& expected,
      const FramePacketHeader& observed) {
    if (expected.packets_in_frame != observed.packets_in_frame) {
      throw std::runtime_error("frame changed packets_in_frame");
    }
    if (expected.radar_id != observed.radar_id) {
      throw std::runtime_error("frame changed radar_id");
    }
    if (expected.data_format != observed.data_format) {
      throw std::runtime_error("frame changed data_format");
    }
  }

  std::size_t max_inflight_frames_;
  std::map<std::uint16_t, InFlightFrame> frames_;
  std::size_t duplicate_fragments_ = 0;
  std::size_t evicted_frames_ = 0;
};

}  // namespace zadar::udp
