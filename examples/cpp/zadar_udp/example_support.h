#pragma once

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <vector>

namespace zadar::udp::examples {

struct RadarOptions {
  std::string bind_address = "0.0.0.0";
  std::uint16_t port = 7777;
  std::size_t frame_limit = 0;
  std::size_t sample_count = 0;
};

struct ImuOptions {
  std::string bind_address = "0.0.0.0";
  std::uint16_t port = 36636;
  std::size_t packet_limit = 0;
};

inline std::uint16_t parse_port(const char* value) {
  const auto parsed = std::strtoul(value, nullptr, 10);
  if (parsed == 0 || parsed > 65535U) {
    std::cerr << "Invalid port: " << value << '\n';
    std::exit(1);
  }
  return static_cast<std::uint16_t>(parsed);
}

inline std::size_t parse_count(const char* value, const char* option_name) {
  char* end = nullptr;
  const auto parsed = std::strtoull(value, &end, 10);
  if (end == value || (end != nullptr && *end != '\0')) {
    std::cerr << "Invalid value for " << option_name << ": " << value << '\n';
    std::exit(1);
  }
  return static_cast<std::size_t>(parsed);
}

inline bool should_stop(std::size_t processed_count, std::size_t limit) {
  return limit > 0 && processed_count >= limit;
}

inline void print_radar_usage(
    const char* program_name,
    const std::string& description,
    bool include_sample_count,
    std::size_t default_sample_count) {
  std::cout << description << "\n\n";
  std::cout << "Usage: " << program_name << " [options]\n\n";
  std::cout << "Options:\n";
  std::cout << "  --bind-address <address>  Local interface to bind for incoming radar UDP traffic. Default: 0.0.0.0\n";
  std::cout << "  --port <port>             Radar UDP port. Default: 7777\n";
  std::cout << "  --frame-limit <count>     Stop after this many completed radar frames. Default: 0\n";
  if (include_sample_count) {
    std::cout << "  --sample-count <count>    Number of items to print from each frame. Default: "
              << default_sample_count << '\n';
  }
  std::cout << "  --help                    Show this help message and exit.\n";
}

inline void print_imu_usage(const char* program_name, const std::string& description) {
  std::cout << description << "\n\n";
  std::cout << "Usage: " << program_name << " [options]\n\n";
  std::cout << "Options:\n";
  std::cout << "  --bind-address <address>  Local interface to bind for incoming IMU UDP traffic. Default: 0.0.0.0\n";
  std::cout << "  --port <port>             IMU UDP port. Default: 36636\n";
  std::cout << "  --packet-limit <count>    Stop after this many decoded IMU packets. Default: 0\n";
  std::cout << "  --help                    Show this help message and exit.\n";
}

inline RadarOptions parse_radar_options(
    int argc,
    char** argv,
    const std::string& description,
    bool include_sample_count = false,
    std::size_t default_sample_count = 0) {
  RadarOptions options;
  options.sample_count = default_sample_count;

  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "--help") {
      print_radar_usage(argv[0], description, include_sample_count, default_sample_count);
      std::exit(0);
    } else if ((arg == "--bind-address") && (i + 1 < argc)) {
      options.bind_address = argv[++i];
    } else if ((arg == "--port") && (i + 1 < argc)) {
      options.port = parse_port(argv[++i]);
    } else if ((arg == "--frame-limit") && (i + 1 < argc)) {
      options.frame_limit = parse_count(argv[++i], "--frame-limit");
    } else if (include_sample_count && (arg == "--sample-count") && (i + 1 < argc)) {
      options.sample_count = parse_count(argv[++i], "--sample-count");
    } else {
      std::cerr << "Unrecognized or incomplete option: " << arg << "\n\n";
      print_radar_usage(argv[0], description, include_sample_count, default_sample_count);
      std::exit(1);
    }
  }
  return options;
}

inline ImuOptions parse_imu_options(int argc, char** argv, const std::string& description) {
  ImuOptions options;
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "--help") {
      print_imu_usage(argv[0], description);
      std::exit(0);
    } else if ((arg == "--bind-address") && (i + 1 < argc)) {
      options.bind_address = argv[++i];
    } else if ((arg == "--port") && (i + 1 < argc)) {
      options.port = parse_port(argv[++i]);
    } else if ((arg == "--packet-limit") && (i + 1 < argc)) {
      options.packet_limit = parse_count(argv[++i], "--packet-limit");
    } else {
      std::cerr << "Unrecognized or incomplete option: " << arg << "\n\n";
      print_imu_usage(argv[0], description);
      std::exit(1);
    }
  }
  return options;
}

inline std::string format_timestamp(
    std::uint64_t timestamp_sec,
    std::uint64_t timestamp_nsec) {
  const auto normalized_sec = timestamp_sec + (timestamp_nsec / 1000000000ULL);
  const auto normalized_nsec = timestamp_nsec % 1000000000ULL;
  const auto milliseconds = normalized_nsec / 1000000ULL;
  const std::time_t wall_time = static_cast<std::time_t>(normalized_sec);
  const std::tm* local_time = std::localtime(&wall_time);

  std::ostringstream formatted_timestamp;
  if (local_time != nullptr) {
    formatted_timestamp << std::put_time(local_time, "%Y-%d-%m %H:%M:%S");
  } else {
    formatted_timestamp << "0000-00-00 00:00:00";
  }
  formatted_timestamp << '.' << std::setw(3) << std::setfill('0') << milliseconds;
  return formatted_timestamp.str();
}

inline std::string format_timestamp_ns(std::uint64_t timestamp_ns) {
  if (timestamp_ns == 0) {
    return "0";
  }
  return format_timestamp(timestamp_ns / 1000000000ULL, timestamp_ns % 1000000000ULL);
}

inline void print_frame_banner(
    std::uint16_t frame_id,
    std::uint64_t timestamp_sec,
    std::uint64_t timestamp_nsec) {
  std::cout << "\n=== Frame #" << frame_id << " ===\n";
  std::cout << "Timestamp: " << format_timestamp(timestamp_sec, timestamp_nsec) << '\n';
}

inline std::vector<std::size_t> sample_indices(
    std::size_t total_count,
    std::size_t sample_count) {
  std::vector<std::size_t> indices(total_count);
  for (std::size_t i = 0; i < total_count; ++i) {
    indices[i] = i;
  }

  std::random_device random_device;
  std::mt19937 generator(random_device());
  std::shuffle(indices.begin(), indices.end(), generator);
  if (indices.size() > sample_count) {
    indices.resize(sample_count);
  }
  return indices;
}

}  // namespace zadar::udp::examples
