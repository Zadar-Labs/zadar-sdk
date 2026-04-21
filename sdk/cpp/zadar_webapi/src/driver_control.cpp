#include "zadar/webapi/driver_control.h"

#include <arpa/inet.h>
#include <cerrno>
#include <netdb.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cstring>
#include <utility>
#include <string>

namespace zadar::webapi {
namespace {

std::string normalize_ip(const std::string& value) {
  const auto start = value.find_first_not_of(" \t\r\n");
  if (start == std::string::npos) {
    return "";
  }
  const auto end = value.find_last_not_of(" \t\r\n");
  return value.substr(start, end - start + 1U);
}

bool is_wildcard_bind_address(const std::string& value) {
  const auto normalized = normalize_ip(value);
  return normalized.empty() || normalized == "0.0.0.0" || normalized == "::";
}

std::string detect_host_ip_for_sensor(
    const std::string& sensor_hostname,
    std::uint16_t webapi_port) {
  const auto sensor_host = normalize_ip(sensor_hostname);
  if (sensor_host.empty()) {
    throw DriverControlError("sensor_hostname must not be empty");
  }

  addrinfo hints{};
  hints.ai_family = AF_INET;
  hints.ai_socktype = SOCK_DGRAM;

  addrinfo* results = nullptr;
  const auto service = std::to_string(webapi_port);
  const int resolve_status =
      ::getaddrinfo(sensor_host.c_str(), service.c_str(), &hints, &results);
  if (resolve_status != 0 || results == nullptr) {
    throw DriverControlError(
        "Unable to resolve sensor hostname '" + sensor_host + "': " +
        gai_strerror(resolve_status));
  }

  const int socket_fd = ::socket(AF_INET, SOCK_DGRAM, 0);
  if (socket_fd < 0) {
    ::freeaddrinfo(results);
    throw DriverControlError(
        "Unable to create a UDP probe socket: " + std::string(std::strerror(errno)));
  }

  std::string local_ip;
  if (::connect(socket_fd, results->ai_addr, results->ai_addrlen) != 0) {
    const std::string error = std::strerror(errno);
    ::close(socket_fd);
    ::freeaddrinfo(results);
    throw DriverControlError(
        "Unable to determine a local host IP for sensor '" + sensor_host + "': " +
        error);
  }

  sockaddr_in local_address{};
  socklen_t local_address_len = sizeof(local_address);
  if (::getsockname(
          socket_fd,
          reinterpret_cast<sockaddr*>(&local_address),
          &local_address_len) != 0) {
    const std::string error = std::strerror(errno);
    ::close(socket_fd);
    ::freeaddrinfo(results);
    throw DriverControlError(
        "Unable to determine a local host IP for sensor '" + sensor_host + "': " +
        error);
  }

  char address_buffer[INET_ADDRSTRLEN] = {};
  const char* printed = ::inet_ntop(
      AF_INET,
      &local_address.sin_addr,
      address_buffer,
      sizeof(address_buffer));
  if (printed == nullptr) {
    const std::string error = std::strerror(errno);
    ::close(socket_fd);
    ::freeaddrinfo(results);
    throw DriverControlError(
        "Unable to determine a local host IP for sensor '" + sensor_host + "': " +
        error);
  }

  local_ip = printed;
  ::close(socket_fd);
  ::freeaddrinfo(results);

  if (local_ip.empty()) {
    throw DriverControlError(
        "Unable to determine a local host IP for sensor '" + sensor_host + "'.");
  }
  return local_ip;
}

std::string extract_error_message(const Response& response) {
  if (!response.error.empty()) {
    return response.error;
  }
  if (!response.body.empty()) {
    return response.body;
  }
  return "HTTP " + std::to_string(response.status_code);
}

}  // namespace

DriverControlError::DriverControlError(const std::string& message, int errnum)
    : std::runtime_error(message),
      errnum_(errnum) {}

int DriverControlError::errnum() const {
  return errnum_;
}

ReservedUdpSocket::ReservedUdpSocket(int fd)
    : fd_(fd) {}

ReservedUdpSocket::~ReservedUdpSocket() {
  close();
}

ReservedUdpSocket::ReservedUdpSocket(ReservedUdpSocket&& other) noexcept
    : fd_(other.fd_) {
  other.fd_ = -1;
}

ReservedUdpSocket& ReservedUdpSocket::operator=(ReservedUdpSocket&& other) noexcept {
  if (this != &other) {
    close();
    fd_ = other.fd_;
    other.fd_ = -1;
  }
  return *this;
}

bool ReservedUdpSocket::is_open() const {
  return fd_ >= 0;
}

void ReservedUdpSocket::close() {
  if (fd_ >= 0) {
    ::close(fd_);
    fd_ = -1;
  }
}

ManagedNetworkSettings resolve_managed_network_settings(
    const std::string& sensor_hostname,
    const std::string& host_ip,
    const std::string& udp_bind_address,
    const std::string& legacy_bind_address,
    std::uint16_t webapi_port) {
  const auto sensor_host = normalize_ip(sensor_hostname);
  if (sensor_host.empty()) {
    throw DriverControlError(
        "sensor_hostname is required for managed single-sensor launch.");
  }

  const auto normalized_host_ip = normalize_ip(host_ip);
  const auto normalized_udp_bind = normalize_ip(udp_bind_address);
  const auto normalized_legacy_bind = normalize_ip(legacy_bind_address);

  std::string destination_ip = normalized_host_ip;
  if (destination_ip.empty() && !is_wildcard_bind_address(normalized_udp_bind)) {
    destination_ip = normalized_udp_bind;
  }
  if (destination_ip.empty() && !is_wildcard_bind_address(normalized_legacy_bind)) {
    destination_ip = normalized_legacy_bind;
  }
  if (destination_ip.empty()) {
    destination_ip = detect_host_ip_for_sensor(sensor_host, webapi_port);
  }

  std::string bind_address = normalized_udp_bind;
  if (bind_address.empty()) {
    bind_address = normalized_legacy_bind;
  }
  if (is_wildcard_bind_address(bind_address)) {
    bind_address = destination_ip;
  }

  return ManagedNetworkSettings{destination_ip, bind_address};
}

ReservedUdpSocket reserve_udp_port(
    const std::string& bind_address,
    std::uint16_t port) {
  const int socket_fd = ::socket(AF_INET, SOCK_DGRAM, 0);
  if (socket_fd < 0) {
    throw DriverControlError(
        "Unable to create a UDP socket while reserving " + bind_address + ":" +
        std::to_string(port) + ": " + std::strerror(errno),
        errno);
  }

  sockaddr_in address{};
  address.sin_family = AF_INET;
  address.sin_port = htons(port);

  const auto normalized_bind_address = normalize_ip(bind_address);
  if (normalized_bind_address.empty() || normalized_bind_address == "0.0.0.0") {
    address.sin_addr.s_addr = INADDR_ANY;
  } else {
    address.sin_addr.s_addr = inet_addr(normalized_bind_address.c_str());
  }

  if (::bind(
          socket_fd,
          reinterpret_cast<const sockaddr*>(&address),
          sizeof(address)) != 0) {
    const int error_number = errno;
    const std::string error = std::strerror(errno);
    ::close(socket_fd);
    throw DriverControlError(
        "Unable to bind UDP port " + std::to_string(port) + " on " +
        normalized_bind_address + ": " + error,
        error_number);
  }

  return ReservedUdpSocket(socket_fd);
}

void require_success(const std::string& action, const Response& response) {
  if (response.success) {
    return;
  }
  throw DriverControlError(action + " failed: " + extract_error_message(response));
}

void configure_sensor_for_udp(
    const Client& client,
    const std::string& destination_ip,
    const std::optional<int>& data_port,
    const std::optional<int>& imu_port,
    const std::optional<int>& running_mode) {
  require_success("Web API heartbeat", client.get_device_clock());
  require_success(
      "Configuring output destination IP",
      client.set_output_destination_ip_address(destination_ip));

  if (data_port.has_value()) {
    require_success(
        "Configuring radar data port",
        client.set_pcl_port(*data_port));
  }
  if (imu_port.has_value()) {
    require_success(
        "Configuring IMU port",
        client.set_imu_port(*imu_port));
  }

  if (running_mode.has_value() && *running_mode >= 0) {
    require_success(
        "Starting running mode " + std::to_string(*running_mode),
        client.set_running_mode(*running_mode));
  }
}

}  // namespace zadar::webapi
