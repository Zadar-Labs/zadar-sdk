#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace zadar::webapi {

struct Response {
  long status_code = 0;
  bool success = false;
  std::string body;
  std::string error;
};

class Client {
 public:
  Client(
      std::string sensor_host,
      std::uint16_t port = 8080,
      std::string api_prefix = "/api/v1",
      long timeout_ms = 5000);

  [[nodiscard]] Response heartbeat() const;
  [[nodiscard]] Response get_device_clock() const;
  [[nodiscard]] Response get_device_modes() const;
  [[nodiscard]] Response get_sensor_info() const;
  [[nodiscard]] Response get_device_ip_address() const;
  [[nodiscard]] Response get_configured_device_ip_address() const;
  [[nodiscard]] Response set_device_ip_address_static(const std::string& ip_address) const;
  [[nodiscard]] Response set_device_ip_address_dhcp() const;
  [[nodiscard]] Response set_configured_device_ip_address_static(
      const std::string& ip_address) const;
  [[nodiscard]] Response reset_configured_device_ip_address() const;
  [[nodiscard]] Response get_current_device_ip_address() const;
  [[nodiscard]] Response get_output_destination_ip_address() const;
  [[nodiscard]] Response set_output_destination_ip_address(const std::string& ip_address) const;
  [[nodiscard]] Response reset_output_destination_ip_address() const;
  [[nodiscard]] Response get_pcl_port() const;
  [[nodiscard]] Response set_pcl_port(int pcl_port) const;
  [[nodiscard]] Response reset_pcl_port() const;
  [[nodiscard]] Response get_imu_port() const;
  [[nodiscard]] Response set_imu_port(int imu_port) const;
  [[nodiscard]] Response reset_imu_port() const;
  [[nodiscard]] Response get_running_mode(long timeout_ms = 5000) const;
  [[nodiscard]] Response set_running_mode(int mode) const;
  [[nodiscard]] Response stop_running_mode() const;
  [[nodiscard]] Response get_startup_mode() const;
  [[nodiscard]] Response set_startup_mode(int mode) const;
  [[nodiscard]] Response reset_startup_mode() const;
  [[nodiscard]] Response get_ptp_sync() const;
  [[nodiscard]] Response get_ptp_sync_status() const;
  [[nodiscard]] Response get_ptp_mode() const;
  [[nodiscard]] Response set_ptp_mode(const std::string& ptp_mode) const;
  [[nodiscard]] Response get_ptp_sync_accuracy() const;
  [[nodiscard]] Response set_ptp_sync_accuracy(int sync_accuracy) const;
  [[nodiscard]] Response get_ptp_trigger_offset() const;
  [[nodiscard]] Response set_ptp_trigger_offset(int trigger_offset) const;
  [[nodiscard]] Response get_diagnostics(long timeout_ms = 10000) const;
  [[nodiscard]] Response reboot() const;

 private:
  [[nodiscard]] Response request(
      const std::string& method,
      const std::string& endpoint,
      const std::optional<std::string>& json_body = std::nullopt,
      std::optional<long> timeout_ms = std::nullopt) const;

  [[nodiscard]] std::string make_url(const std::string& endpoint) const;

  std::string sensor_host_;
  std::uint16_t port_;
  std::string api_prefix_;
  long timeout_ms_;
};

}  // namespace zadar::webapi
