#pragma once

#include <cstdint>
#include <optional>
#include <stdexcept>
#include <string>

#include "zadar/webapi/client.h"

namespace zadar::webapi {

constexpr std::uint16_t kDefaultDataPort = 7777U;
constexpr std::uint16_t kDefaultImuPort = 36636U;
constexpr std::uint16_t kDefaultWebApiPort = 8080U;

class DriverControlError : public std::runtime_error {
 public:
  explicit DriverControlError(const std::string& message, int errnum = 0);

  [[nodiscard]] int errnum() const;

 private:
  int errnum_ = 0;
};

class ReservedUdpSocket {
 public:
  ReservedUdpSocket() = default;
  explicit ReservedUdpSocket(int fd);
  ~ReservedUdpSocket();

  ReservedUdpSocket(const ReservedUdpSocket&) = delete;
  ReservedUdpSocket& operator=(const ReservedUdpSocket&) = delete;
  ReservedUdpSocket(ReservedUdpSocket&& other) noexcept;
  ReservedUdpSocket& operator=(ReservedUdpSocket&& other) noexcept;

  [[nodiscard]] bool is_open() const;
  void close();

 private:
  int fd_ = -1;
};

struct ManagedNetworkSettings {
  std::string destination_ip;
  std::string bind_address;
};

ManagedNetworkSettings resolve_managed_network_settings(
    const std::string& sensor_hostname,
    const std::string& host_ip,
    const std::string& udp_bind_address,
    const std::string& legacy_bind_address,
    std::uint16_t webapi_port = kDefaultWebApiPort);

ReservedUdpSocket reserve_udp_port(
    const std::string& bind_address,
    std::uint16_t port);

void require_success(const std::string& action, const Response& response);

void configure_sensor_for_udp(
    const Client& client,
    const std::string& destination_ip,
    const std::optional<int>& data_port,
    const std::optional<int>& imu_port,
    const std::optional<int>& running_mode);

}  // namespace zadar::webapi
