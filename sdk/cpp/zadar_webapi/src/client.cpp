#include "zadar/webapi/client.h"

#include <curl/curl.h>

#include <optional>
#include <sstream>
#include <string>

namespace zadar::webapi {
namespace {

struct CurlGlobalInit {
  CurlGlobalInit() {
    curl_global_init(CURL_GLOBAL_DEFAULT);
  }

  ~CurlGlobalInit() {
    curl_global_cleanup();
  }
};

CurlGlobalInit g_curl_global_init;

std::size_t write_callback(char* ptr, std::size_t size, std::size_t nmemb, void* userdata) {
  auto* output = static_cast<std::string*>(userdata);
  output->append(ptr, size * nmemb);
  return size * nmemb;
}

std::string json_string(const std::string& value) {
  std::string output;
  output.reserve(value.size() + 2U);
  output.push_back('"');
  for (char ch : value) {
    if (ch == '"' || ch == '\\') {
      output.push_back('\\');
    }
    output.push_back(ch);
  }
  output.push_back('"');
  return output;
}

}  // namespace

Client::Client(
    std::string sensor_host,
    std::uint16_t port,
    std::string api_prefix,
    long timeout_ms)
    : sensor_host_(std::move(sensor_host)),
      port_(port),
      api_prefix_(std::move(api_prefix)),
      timeout_ms_(timeout_ms) {
  if (!api_prefix_.empty() && api_prefix_.front() != '/') {
    api_prefix_.insert(api_prefix_.begin(), '/');
  }
}

std::string Client::make_url(const std::string& endpoint) const {
  std::ostringstream stream;
  stream << "http://" << sensor_host_ << ':' << port_;
  if (!api_prefix_.empty()) {
    stream << api_prefix_;
  }
  if (!endpoint.empty() && endpoint.front() != '/') {
    stream << '/';
  }
  stream << endpoint;
  return stream.str();
}

Response Client::request(
    const std::string& method,
    const std::string& endpoint,
    const std::optional<std::string>& json_body,
    std::optional<long> timeout_ms) const {
  CURL* handle = curl_easy_init();
  if (handle == nullptr) {
    return Response{0, false, "", "Failed to initialize CURL."};
  }

  std::string response_body;
  struct curl_slist* headers = nullptr;
  if (json_body.has_value()) {
    headers = curl_slist_append(headers, "Content-Type: application/json");
  }

  curl_easy_setopt(handle, CURLOPT_URL, make_url(endpoint).c_str());
  curl_easy_setopt(handle, CURLOPT_FOLLOWLOCATION, 1L);
  curl_easy_setopt(handle, CURLOPT_WRITEFUNCTION, &write_callback);
  curl_easy_setopt(handle, CURLOPT_WRITEDATA, &response_body);
  curl_easy_setopt(handle, CURLOPT_TIMEOUT_MS, timeout_ms.value_or(timeout_ms_));

  if (method == "POST") {
    curl_easy_setopt(handle, CURLOPT_POST, 1L);
  } else if (method != "GET") {
    curl_easy_setopt(handle, CURLOPT_CUSTOMREQUEST, method.c_str());
  }

  if (json_body.has_value()) {
    curl_easy_setopt(handle, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(handle, CURLOPT_POSTFIELDS, json_body->c_str());
  }

  const CURLcode curl_code = curl_easy_perform(handle);
  long status_code = 0;
  curl_easy_getinfo(handle, CURLINFO_RESPONSE_CODE, &status_code);

  if (headers != nullptr) {
    curl_slist_free_all(headers);
  }
  curl_easy_cleanup(handle);

  if (curl_code != CURLE_OK) {
    return Response{
        status_code,
        false,
        response_body,
        curl_easy_strerror(curl_code),
    };
  }

  return Response{
      status_code,
      status_code >= 200 && status_code < 300,
      response_body,
      "",
  };
}

Response Client::heartbeat() const {
  return get_device_clock();
}

Response Client::get_device_clock() const {
  return request("GET", "device/clock");
}

Response Client::get_device_modes() const {
  return request("GET", "device/modes");
}

Response Client::get_sensor_info() const {
  return request("GET", "device/system/sensor_info");
}

Response Client::get_device_ip_address() const {
  return get_configured_device_ip_address();
}

Response Client::get_configured_device_ip_address() const {
  return request("GET", "system/network/ipv4/address");
}

Response Client::set_device_ip_address_static(const std::string& ip_address) const {
  return set_configured_device_ip_address_static(ip_address);
}

Response Client::set_configured_device_ip_address_static(const std::string& ip_address) const {
  return request(
      "PUT",
      "system/network/ipv4/address",
      std::string("{\"ip_address\":") + json_string(ip_address) + "}");
}

Response Client::set_device_ip_address_dhcp() const {
  return reset_configured_device_ip_address();
}

Response Client::reset_configured_device_ip_address() const {
  return request("DELETE", "system/network/ipv4/address");
}

Response Client::get_current_device_ip_address() const {
  return request("GET", "device/network/ipv4/address");
}

Response Client::get_output_destination_ip_address() const {
  return request("GET", "system/output_destination/ipaddress");
}

Response Client::set_output_destination_ip_address(const std::string& ip_address) const {
  return request(
      "PUT",
      "system/output_destination/ipaddress",
      std::string("{\"ip_address\":") + json_string(ip_address) + "}");
}

Response Client::reset_output_destination_ip_address() const {
  return request("DELETE", "system/output_destination/ipaddress");
}

Response Client::get_pcl_port() const {
  return request("GET", "system/output_destination/pcl/port");
}

Response Client::set_pcl_port(int pcl_port) const {
  return request(
      "PUT",
      "system/output_destination/pcl/port",
      std::string("{\"pcl_port\":") + std::to_string(pcl_port) + "}");
}

Response Client::reset_pcl_port() const {
  return request("DELETE", "system/output_destination/pcl/port");
}

Response Client::get_imu_port() const {
  return request("GET", "system/output_destination/imu/port");
}

Response Client::set_imu_port(int imu_port) const {
  return request(
      "PUT",
      "system/output_destination/imu/port",
      std::string("{\"imu_port\":") + std::to_string(imu_port) + "}");
}

Response Client::reset_imu_port() const {
  return request("DELETE", "system/output_destination/imu/port");
}

Response Client::get_running_mode(long timeout_ms) const {
  return request("GET", "device/running_mode", std::nullopt, timeout_ms);
}

Response Client::set_running_mode(int mode) const {
  return request(
      "POST",
      "device/running_mode",
      std::string("{\"mode\":") + std::to_string(mode) + "}");
}

Response Client::stop_running_mode() const {
  return request("POST", "device/running_mode/stop");
}

Response Client::get_startup_mode() const {
  return request("GET", "system/startup_mode");
}

Response Client::set_startup_mode(int mode) const {
  return request(
      "PUT",
      "system/startup_mode",
      std::string("{\"mode\":") + std::to_string(mode) + "}");
}

Response Client::reset_startup_mode() const {
  return request("DELETE", "system/startup_mode");
}

Response Client::get_ptp_sync() const {
  return get_ptp_sync_status();
}

Response Client::get_ptp_sync_status() const {
  return request("GET", "device/ptp_sync");
}

Response Client::get_ptp_mode() const {
  return request("GET", "system/ptp/mode");
}

Response Client::set_ptp_mode(const std::string& ptp_mode) const {
  return request(
      "PUT",
      "system/ptp/mode",
      std::string("{\"ptp_mode\":") + json_string(ptp_mode) + "}");
}

Response Client::get_ptp_sync_accuracy() const {
  return request("GET", "system/ptp/sync_accuracy");
}

Response Client::set_ptp_sync_accuracy(int sync_accuracy) const {
  return request(
      "PUT",
      "system/ptp/sync_accuracy",
      std::string("{\"sync_accuracy\":") + std::to_string(sync_accuracy) + "}");
}

Response Client::get_ptp_trigger_offset() const {
  return request("GET", "system/ptp/trigger_offset");
}

Response Client::set_ptp_trigger_offset(int trigger_offset) const {
  return request(
      "PUT",
      "system/ptp/trigger_offset",
      std::string("{\"trigger_offset\":") + std::to_string(trigger_offset) + "}");
}

Response Client::get_diagnostics(long timeout_ms) const {
  return request("GET", "device/system/diagnostics", std::nullopt, timeout_ms);
}

Response Client::reboot() const {
  return request("PUT", "device/reboot");
}

}  // namespace zadar::webapi
