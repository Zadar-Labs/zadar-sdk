#include <geometry_msgs/Point32.h>
#include <ros/ros.h>
#include <sensor_msgs/Imu.h>
#include <sensor_msgs/PointCloud2.h>
#include <sensor_msgs/PointField.h>
#include <std_msgs/Header.h>
#include <zadar_msgs/ZadarCluster.h>
#include <zadar_msgs/ZadarClusters.h>
#include <zadar_msgs/ZadarOdometry.h>
#include <zadar_msgs/ZadarTrack.h>
#include <zadar_msgs/ZadarTracks.h>

#include <atomic>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <thread>
#include <tuple>
#include <utility>
#include <vector>

#include "zadar/udp/imu_listener.h"
#include "zadar/udp/radar_listener.h"
#include "zadar/webapi/client.h"
#include "zadar/webapi/driver_control.h"

namespace {

constexpr std::size_t kPointStep = 54U;

ros::Time ros_time_from_ns(std::uint64_t timestamp_ns) {
  return ros::Time(
      static_cast<std::uint32_t>(timestamp_ns / 1000000000ULL),
      static_cast<std::uint32_t>(timestamp_ns % 1000000000ULL));
}

ros::Time ros_time_from_sec_nsec(
    std::uint64_t timestamp_sec,
    std::uint64_t timestamp_nsec) {
  return ros::Time(
      static_cast<std::uint32_t>(timestamp_sec),
      static_cast<std::uint32_t>(timestamp_nsec));
}

std_msgs::Header header_from_ns(
    const std::string& frame_id,
    std::uint64_t timestamp_ns) {
  std_msgs::Header header;
  header.frame_id = frame_id;
  header.stamp = ros_time_from_ns(timestamp_ns);
  return header;
}

std::uint64_t frame_timestamp_ns(const zadar::udp::Timestamp& timestamp) {
  return timestamp.sec * 1000000000ULL + timestamp.nsec;
}

std::uint64_t scan_timestamp_ns(
    const zadar_pb::RadarScan& radar_scan,
    std::uint64_t fallback_timestamp_ns) {
  return radar_scan.header().stamp() > 0
             ? radar_scan.header().stamp()
             : fallback_timestamp_ns;
}

sensor_msgs::PointField point_field(
    const std::string& name,
    std::uint32_t offset,
    std::uint8_t datatype) {
  sensor_msgs::PointField field;
  field.name = name;
  field.offset = offset;
  field.datatype = datatype;
  field.count = 1;
  return field;
}

template <typename T>
void write_value(std::vector<std::uint8_t>& data, std::size_t offset, const T& value) {
  std::memcpy(data.data() + offset, &value, sizeof(T));
}

sensor_msgs::PointCloud2 radar_scan_to_pointcloud2(
    const zadar_pb::RadarScan& radar_scan,
    const std::string& frame_id,
    std::uint64_t fallback_timestamp_ns) {
  sensor_msgs::PointCloud2 message;
  message.header = header_from_ns(
      frame_id,
      scan_timestamp_ns(radar_scan, fallback_timestamp_ns));
  message.is_bigendian = false;
  message.is_dense = radar_scan.is_dense();

  message.fields = {
      point_field("x", 0U, sensor_msgs::PointField::FLOAT32),
      point_field("y", 4U, sensor_msgs::PointField::FLOAT32),
      point_field("z", 8U, sensor_msgs::PointField::FLOAT32),
      point_field("snr", 12U, sensor_msgs::PointField::FLOAT32),
      point_field("range", 16U, sensor_msgs::PointField::FLOAT32),
      point_field("noise", 20U, sensor_msgs::PointField::FLOAT32),
      point_field("doppler", 24U, sensor_msgs::PointField::FLOAT32),
      point_field("adjusted_doppler", 28U, sensor_msgs::PointField::FLOAT32),
      point_field("frame_num", 32U, sensor_msgs::PointField::UINT32),
      point_field("is_static", 36U, sensor_msgs::PointField::UINT8),
      point_field("removed", 37U, sensor_msgs::PointField::UINT8),
      point_field("subframe_index", 38U, sensor_msgs::PointField::UINT32),
      point_field("fence_id", 42U, sensor_msgs::PointField::UINT32),
      point_field("power", 46U, sensor_msgs::PointField::FLOAT32),
      point_field("rcs", 50U, sensor_msgs::PointField::FLOAT32),
  };
  message.point_step = kPointStep;

  const auto point_count = static_cast<std::size_t>(radar_scan.points_size());
  std::uint32_t width = radar_scan.width() > 0
                            ? static_cast<std::uint32_t>(radar_scan.width())
                            : static_cast<std::uint32_t>(point_count);
  std::uint32_t height = radar_scan.height() > 0
                             ? static_cast<std::uint32_t>(radar_scan.height())
                             : 1U;
  if (static_cast<std::size_t>(width) * static_cast<std::size_t>(height) != point_count) {
    width = static_cast<std::uint32_t>(point_count);
    height = 1U;
  }

  message.width = width;
  message.height = height;
  message.row_step = message.point_step * message.width;
  message.data.resize(message.point_step * point_count);

  for (std::size_t index = 0; index < point_count; ++index) {
    const auto& point = radar_scan.points(static_cast<int>(index));
    const std::size_t base = index * message.point_step;

    const float x = point.x();
    const float y = point.y();
    const float z = point.z();
    const float snr = point.snr();
    const float range = point.range();
    const float noise = point.noise();
    const float doppler = point.doppler();
    const float adjusted_doppler = point.adjusted_doppler();
    const std::uint32_t frame_num = point.frame_num();
    const std::uint8_t is_static = point.is_static() ? 1U : 0U;
    const std::uint8_t removed = point.removed() ? 1U : 0U;
    const std::uint32_t subframe_index = point.subframe_index();
    const std::uint32_t fence_id = point.fence_id();
    const float power = point.power();
    const float rcs = point.rcs();

    write_value(message.data, base + 0U, x);
    write_value(message.data, base + 4U, y);
    write_value(message.data, base + 8U, z);
    write_value(message.data, base + 12U, snr);
    write_value(message.data, base + 16U, range);
    write_value(message.data, base + 20U, noise);
    write_value(message.data, base + 24U, doppler);
    write_value(message.data, base + 28U, adjusted_doppler);
    write_value(message.data, base + 32U, frame_num);
    write_value(message.data, base + 36U, is_static);
    write_value(message.data, base + 37U, removed);
    write_value(message.data, base + 38U, subframe_index);
    write_value(message.data, base + 42U, fence_id);
    write_value(message.data, base + 46U, power);
    write_value(message.data, base + 50U, rcs);
  }

  return message;
}

std::vector<geometry_msgs::Point32> vertices_to_msg(
    const google::protobuf::RepeatedPtrField<zadar_pb::ZadarVertex>& vertices) {
  std::vector<geometry_msgs::Point32> converted;
  converted.reserve(static_cast<std::size_t>(vertices.size()));
  for (const auto& vertex : vertices) {
    geometry_msgs::Point32 point;
    point.x = vertex.x();
    point.y = vertex.y();
    point.z = vertex.z();
    converted.push_back(point);
  }
  return converted;
}

zadar_msgs::ZadarClusters clusters_to_msg(
    const google::protobuf::RepeatedPtrField<zadar_pb::ZadarCluster>& clusters,
    const std::string& frame_id,
    std::uint64_t timestamp_ns) {
  zadar_msgs::ZadarClusters message;
  message.header = header_from_ns(frame_id, timestamp_ns);
  message.frame_num = clusters.size() == 0 ? 0U : clusters.Get(0).frame_num();
  message.clusters.reserve(static_cast<std::size_t>(clusters.size()));

  for (const auto& cluster : clusters) {
    zadar_msgs::ZadarCluster cluster_message;
    cluster_message.cluster_id = cluster.cluster_id();
    cluster_message.frame_num = cluster.frame_num();
    cluster_message.subframe_index = cluster.subframe_index();
    cluster_message.is_static = cluster.is_static();
    cluster_message.x = cluster.x();
    cluster_message.y = cluster.y();
    cluster_message.z = cluster.z();
    cluster_message.doppler = cluster.doppler();
    cluster_message.snr = cluster.snr();
    cluster_message.noise = cluster.noise();
    cluster_message.d_min = cluster.d_min();
    cluster_message.d_max = cluster.d_max();
    cluster_message.r_min = cluster.r_min();
    cluster_message.r_max = cluster.r_max();
    cluster_message.lambda1 = cluster.lambda1();
    cluster_message.lambda2 = cluster.lambda2();
    cluster_message.lambda3 = cluster.lambda3();
    cluster_message.num_points = cluster.num_points();
    cluster_message.vertices = vertices_to_msg(cluster.vertices());
    cluster_message.scan = radar_scan_to_pointcloud2(cluster.scan(), frame_id, timestamp_ns);
    message.clusters.push_back(std::move(cluster_message));
  }

  return message;
}

zadar_msgs::ZadarTracks tracks_to_msg(
    const google::protobuf::RepeatedPtrField<zadar_pb::ZadarTrack>& tracks,
    const std::string& frame_id,
    std::uint64_t timestamp_ns,
    std::uint64_t frame_number) {
  zadar_msgs::ZadarTracks message;
  message.header = header_from_ns(frame_id, timestamp_ns);
  message.frame_num = frame_number;
  message.tracks.reserve(static_cast<std::size_t>(tracks.size()));

  for (const auto& track : tracks) {
    zadar_msgs::ZadarTrack track_message;
    track_message.track_id = track.track_id();
    track_message.x = track.x();
    track_message.y = track.y();
    track_message.z = track.z();
    track_message.vx = track.vx();
    track_message.vy = track.vy();
    track_message.vz = track.vz();
    track_message.ax = track.ax();
    track_message.ay = track.ay();
    track_message.az = track.az();
    track_message.yaw = track.yaw();
    track_message.speed = track.speed();
    track_message.num_points = track.num_points();
    track_message.latest_observed_frame_num = track.latest_observed_frame_num();
    track_message.latest_cluster_id = track.latest_cluster_id();
    track_message.state = track.state();
    track_message.classification_output = track.classification_output();
    track_message.fence_id = track.fence_id();
    track_message.scan = radar_scan_to_pointcloud2(track.scan(), frame_id, timestamp_ns);
    message.tracks.push_back(std::move(track_message));
  }

  return message;
}

zadar_msgs::ZadarOdometry odometry_to_msg(
    const zadar_pb::ZadarOdometry& odometry,
    const std::string& frame_id,
    std::uint64_t fallback_timestamp_ns) {
  const std::uint64_t timestamp_ns =
      odometry.stamp() > 0 ? odometry.stamp() : fallback_timestamp_ns;

  zadar_msgs::ZadarOdometry message;
  message.header = header_from_ns(frame_id, timestamp_ns);
  message.sensor_stamp = timestamp_ns;
  message.frame_num = odometry.frame_num();
  message.raw_vx = odometry.raw_vx();
  message.raw_vy = odometry.raw_vy();
  message.raw_vz = odometry.raw_vz();
  message.vx = odometry.vx();
  message.vy = odometry.vy();
  message.vz = odometry.vz();
  message.phi = odometry.phi();
  message.psi = odometry.psi();
  message.theta = odometry.theta();
  message.omega_x = odometry.omega_x();
  message.omega_y = odometry.omega_y();
  message.omega_z = odometry.omega_z();
  return message;
}

sensor_msgs::Imu imu_to_msg(
    const zadar::udp::ImuDataPayload& payload,
    const std::string& frame_id) {
  sensor_msgs::Imu message;
  message.header.frame_id = frame_id;
  message.header.stamp = ros_time_from_sec_nsec(
      payload.timestamp.sec,
      payload.timestamp.nsec);

  message.orientation_covariance[0] = -1.0;
  message.angular_velocity_covariance[0] = -1.0;
  message.linear_acceleration_covariance[0] = -1.0;

  message.linear_acceleration.x = payload.packet.acceleration_x;
  message.linear_acceleration.y = payload.packet.acceleration_y;
  message.linear_acceleration.z = payload.packet.acceleration_z;
  message.angular_velocity.x = payload.packet.angular_rate_x;
  message.angular_velocity.y = payload.packet.angular_rate_y;
  message.angular_velocity.z = payload.packet.angular_rate_z;
  return message;
}

class ZadarUdpDriverNode {
 public:
  ZadarUdpDriverNode()
      : nh_(),
        private_nh_("~") {
    private_nh_.param<std::string>("udp_bind_address", configured_udp_bind_address_, "");
    private_nh_.param<std::string>("bind_address", configured_legacy_bind_address_, "");
    private_nh_.param<std::string>("sensor_hostname", sensor_hostname_, "");
    private_nh_.param<std::string>("host_ip", host_ip_, "");
    managed_mode_ = !sensor_hostname_.empty();

    bind_address_ = !configured_udp_bind_address_.empty()
                        ? configured_udp_bind_address_
                        : configured_legacy_bind_address_;
    if (bind_address_.empty()) {
      bind_address_ = "0.0.0.0";
    }
    if (!configured_legacy_bind_address_.empty() &&
        configured_udp_bind_address_.empty() &&
        configured_legacy_bind_address_ != "0.0.0.0") {
      ROS_WARN("Parameter 'bind_address' is deprecated; prefer 'udp_bind_address'.");
    }

    int data_port = 0;
    int imu_port = 0;
    int webapi_port = static_cast<int>(zadar::webapi::kDefaultWebApiPort);
    int radar_socket_buffer_bytes = 64 * 1024 * 1024;
    int imu_socket_buffer_bytes = 4 * 1024 * 1024;
    int max_buffered_frames = 128;
    std::string generated_python_dir;

    private_nh_.param("data_port", data_port, 0);
    private_nh_.param("imu_port", imu_port, 0);
    private_nh_.param("webapi_port", webapi_port, static_cast<int>(zadar::webapi::kDefaultWebApiPort));
    private_nh_.param("webapi_timeout_sec", webapi_timeout_sec_, 5.0);
    private_nh_.param("running_mode", running_mode_, -1);
    private_nh_.param("frame_id", frame_id_, std::string("zadar"));
    private_nh_.param("publish_scan", publish_scan_, true);
    private_nh_.param("publish_clusters", publish_clusters_, true);
    private_nh_.param("publish_tracks", publish_tracks_, true);
    private_nh_.param("publish_odometry", publish_odometry_, true);
    private_nh_.param("publish_imu", publish_imu_, true);
    private_nh_.param("radar_socket_buffer_bytes", radar_socket_buffer_bytes, 64 * 1024 * 1024);
    private_nh_.param("imu_socket_buffer_bytes", imu_socket_buffer_bytes, 4 * 1024 * 1024);
    private_nh_.param("max_buffered_frames", max_buffered_frames, 128);
    private_nh_.param("frame_timeout_sec", frame_timeout_sec_, 1.0);
    private_nh_.param("socket_timeout_sec", socket_timeout_sec_, 0.25);
    private_nh_.param("generated_python_dir", generated_python_dir, std::string());

    if (data_port < 0 || data_port > 65535) {
      throw std::invalid_argument("data_port must be between 0 and 65535.");
    }
    if (imu_port < 0 || imu_port > 65535) {
      throw std::invalid_argument("imu_port must be between 0 and 65535.");
    }
    if (webapi_port <= 0 || webapi_port > 65535) {
      throw std::invalid_argument("webapi_port must be between 1 and 65535.");
    }

    requested_data_port_ = static_cast<std::uint16_t>(data_port);
    requested_imu_port_ = static_cast<std::uint16_t>(imu_port);
    webapi_port_ = static_cast<std::uint16_t>(webapi_port);
    radar_socket_buffer_bytes_ = static_cast<std::size_t>(radar_socket_buffer_bytes);
    imu_socket_buffer_bytes_ = static_cast<std::size_t>(imu_socket_buffer_bytes);
    max_buffered_frames_ = static_cast<std::size_t>(max_buffered_frames);

    if (!generated_python_dir.empty()) {
      ROS_WARN("Parameter 'generated_python_dir' is ignored by the C++ driver.");
    }

    radar_stream_enabled_ =
        publish_scan_ || publish_clusters_ || publish_tracks_ || publish_odometry_;
    imu_stream_enabled_ = publish_imu_;

    if (running_mode_ >= 0 && !managed_mode_) {
      throw std::invalid_argument(
          "running_mode requires sensor_hostname so the driver can control the sensor.");
    }
    if (!host_ip_.empty() && !managed_mode_) {
      ROS_WARN("Parameter 'host_ip' is ignored unless sensor_hostname is provided.");
    }

    if (publish_scan_) {
      points_publisher_ = nh_.advertise<sensor_msgs::PointCloud2>("points", 10);
    }
    if (publish_clusters_) {
      clusters_publisher_ = nh_.advertise<zadar_msgs::ZadarClusters>("clusters", 10);
    }
    if (publish_tracks_) {
      tracks_publisher_ = nh_.advertise<zadar_msgs::ZadarTracks>("tracks", 10);
    }
    if (publish_odometry_) {
      odometry_publisher_ = nh_.advertise<zadar_msgs::ZadarOdometry>("odometry", 10);
    }
    if (publish_imu_) {
      imu_publisher_ = nh_.advertise<sensor_msgs::Imu>("imu", 10);
    }

    if (managed_mode_) {
      prepare_managed_single_sensor();
    } else {
      prepare_receive_only();
    }
    start_workers();
    log_launch_configuration();
  }

  ~ZadarUdpDriverNode() {
    stop();
  }

  void stop() {
    const bool already_stopping = stop_requested_.exchange(true);
    if (already_stopping) {
      return;
    }

    if (radar_listener_ != nullptr) {
      radar_listener_->close();
    }
    if (imu_listener_ != nullptr) {
      imu_listener_->close();
    }

    for (auto& thread : threads_) {
      if (thread.joinable()) {
        thread.join();
      }
    }
  }

 private:
  std::unique_ptr<zadar::udp::RadarDataListener> make_radar_listener(
      std::uint16_t port) const {
    return std::make_unique<zadar::udp::RadarDataListener>(
        bind_address_,
        port,
        radar_socket_buffer_bytes_,
        max_buffered_frames_,
        frame_timeout_sec_,
        socket_timeout_sec_ > 0.0 ? std::optional<double>(socket_timeout_sec_)
                                  : std::nullopt);
  }

  std::unique_ptr<zadar::udp::ImuDataListener> make_imu_listener(
      std::uint16_t port) const {
    return std::make_unique<zadar::udp::ImuDataListener>(
        bind_address_,
        port,
        imu_socket_buffer_bytes_,
        socket_timeout_sec_ > 0.0 ? std::optional<double>(socket_timeout_sec_)
                                  : std::nullopt);
  }

  void prepare_receive_only() {
    data_port_ = requested_data_port_ > 0 ? requested_data_port_
                                          : zadar::webapi::kDefaultDataPort;
    imu_port_ = requested_imu_port_ > 0 ? requested_imu_port_
                                        : zadar::webapi::kDefaultImuPort;

    if (radar_stream_enabled_) {
      radar_listener_ = make_radar_listener(data_port_);
    }
    if (imu_stream_enabled_) {
      imu_listener_ = make_imu_listener(imu_port_);
    }
  }

  void prepare_managed_single_sensor() {
    const auto network_settings = zadar::webapi::resolve_managed_network_settings(
        sensor_hostname_,
        host_ip_,
        configured_udp_bind_address_,
        configured_legacy_bind_address_,
        webapi_port_);
    destination_ip_ = network_settings.destination_ip;
    bind_address_ = network_settings.bind_address;

    if (!radar_stream_enabled_ && requested_data_port_ > 0) {
      ROS_WARN("data_port was provided but radar publishers are disabled; the radar port is ignored.");
    }
    if (!imu_stream_enabled_ && requested_imu_port_ > 0) {
      ROS_WARN("imu_port was provided but IMU publishing is disabled; the IMU port is ignored.");
    }

    if (radar_stream_enabled_ && imu_stream_enabled_) {
      std::tie(data_port_, imu_port_, radar_listener_, imu_listener_) =
          reserve_listener_pair();
    } else if (radar_stream_enabled_) {
      std::tie(data_port_, radar_listener_) = reserve_radar_listener();
    } else if (imu_stream_enabled_) {
      std::tie(imu_port_, imu_listener_) = reserve_imu_listener();
    }

    const auto timeout_ms = static_cast<long>(webapi_timeout_sec_ * 1000.0);
    const zadar::webapi::Client client(
        sensor_hostname_,
        webapi_port_,
        "/api/v1",
        timeout_ms);
    zadar::webapi::configure_sensor_for_udp(
        client,
        destination_ip_,
        radar_stream_enabled_ ? std::optional<int>(data_port_) : std::nullopt,
        imu_stream_enabled_ ? std::optional<int>(imu_port_) : std::nullopt,
        running_mode_ >= 0 ? std::optional<int>(running_mode_) : std::nullopt);
  }

  std::pair<std::uint16_t, std::unique_ptr<zadar::udp::RadarDataListener>>
  reserve_radar_listener() {
    const bool explicit_port = requested_data_port_ > 0;
    const std::uint16_t start_port =
        explicit_port ? requested_data_port_ : zadar::webapi::kDefaultDataPort;
    std::string last_error;

    for (std::uint32_t candidate = start_port; candidate < start_port + 256U; ++candidate) {
      try {
        auto reservation =
            zadar::webapi::reserve_udp_port(bind_address_, static_cast<std::uint16_t>(candidate));
        auto listener = make_radar_listener(static_cast<std::uint16_t>(candidate));
        reservation.close();
        listener->open();
        return {
            static_cast<std::uint16_t>(candidate),
            std::move(listener),
        };
      } catch (const zadar::webapi::DriverControlError& error) {
        if (explicit_port || error.errnum() != EADDRINUSE) {
          throw;
        }
        last_error = error.what();
      } catch (const std::exception& error) {
        throw zadar::webapi::DriverControlError(
            "Unable to bind radar UDP listener on " + bind_address_ + ":" +
            std::to_string(candidate) + ": " + error.what());
      }
    }

    throw zadar::webapi::DriverControlError(
        "Unable to allocate an available radar UDP port starting from " +
        std::to_string(start_port) + ": " + last_error);
  }

  std::pair<std::uint16_t, std::unique_ptr<zadar::udp::ImuDataListener>>
  reserve_imu_listener() {
    const bool explicit_port = requested_imu_port_ > 0;
    const std::uint16_t start_port =
        explicit_port ? requested_imu_port_ : zadar::webapi::kDefaultImuPort;
    std::string last_error;

    for (std::uint32_t candidate = start_port; candidate < start_port + 256U; ++candidate) {
      try {
        auto reservation =
            zadar::webapi::reserve_udp_port(bind_address_, static_cast<std::uint16_t>(candidate));
        auto listener = make_imu_listener(static_cast<std::uint16_t>(candidate));
        reservation.close();
        listener->open();
        return {
            static_cast<std::uint16_t>(candidate),
            std::move(listener),
        };
      } catch (const zadar::webapi::DriverControlError& error) {
        if (explicit_port || error.errnum() != EADDRINUSE) {
          throw;
        }
        last_error = error.what();
      } catch (const std::exception& error) {
        throw zadar::webapi::DriverControlError(
            "Unable to bind IMU UDP listener on " + bind_address_ + ":" +
            std::to_string(candidate) + ": " + error.what());
      }
    }

    throw zadar::webapi::DriverControlError(
        "Unable to allocate an available IMU UDP port starting from " +
        std::to_string(start_port) + ": " + last_error);
  }

  std::tuple<
      std::uint16_t,
      std::uint16_t,
      std::unique_ptr<zadar::udp::RadarDataListener>,
      std::unique_ptr<zadar::udp::ImuDataListener>>
  reserve_listener_pair() {
    const bool data_explicit = requested_data_port_ > 0;
    const bool imu_explicit = requested_imu_port_ > 0;

    if (data_explicit && imu_explicit) {
      return reserve_explicit_pair(requested_data_port_, requested_imu_port_);
    }

    if (data_explicit) {
      for (std::uint32_t imu_port = zadar::webapi::kDefaultImuPort;
           imu_port < zadar::webapi::kDefaultImuPort + 256U;
           ++imu_port) {
        auto pair = try_reserve_pair(
            requested_data_port_,
            static_cast<std::uint16_t>(imu_port));
        if (pair.has_value()) {
          return std::move(*pair);
        }
      }
      throw zadar::webapi::DriverControlError(
          "Unable to allocate an IMU UDP port starting from " +
          std::to_string(zadar::webapi::kDefaultImuPort) +
          " while using explicit radar port " +
          std::to_string(requested_data_port_) + ".");
    }

    if (imu_explicit) {
      for (std::uint32_t data_port = zadar::webapi::kDefaultDataPort;
           data_port < zadar::webapi::kDefaultDataPort + 256U;
           ++data_port) {
        auto pair = try_reserve_pair(
            static_cast<std::uint16_t>(data_port),
            requested_imu_port_);
        if (pair.has_value()) {
          return std::move(*pair);
        }
      }
      throw zadar::webapi::DriverControlError(
          "Unable to allocate a radar UDP port starting from " +
          std::to_string(zadar::webapi::kDefaultDataPort) +
          " while using explicit IMU port " +
          std::to_string(requested_imu_port_) + ".");
    }

    for (std::uint32_t offset = 0; offset < 256U; ++offset) {
      auto pair = try_reserve_pair(
          static_cast<std::uint16_t>(zadar::webapi::kDefaultDataPort + offset),
          static_cast<std::uint16_t>(zadar::webapi::kDefaultImuPort + offset));
      if (pair.has_value()) {
        return std::move(*pair);
      }
    }

    throw zadar::webapi::DriverControlError(
        "Unable to allocate a managed radar/IMU UDP port pair.");
  }

  std::tuple<
      std::uint16_t,
      std::uint16_t,
      std::unique_ptr<zadar::udp::RadarDataListener>,
      std::unique_ptr<zadar::udp::ImuDataListener>>
  reserve_explicit_pair(
      std::uint16_t data_port,
      std::uint16_t imu_port) {
    auto pair = try_reserve_pair(data_port, imu_port, false);
    if (!pair.has_value()) {
      throw zadar::webapi::DriverControlError(
          "Unable to bind the requested UDP ports " +
          std::to_string(data_port) + " and " + std::to_string(imu_port) +
          " on " + bind_address_ + ".");
    }
    return std::move(*pair);
  }

  std::optional<
      std::tuple<
          std::uint16_t,
          std::uint16_t,
          std::unique_ptr<zadar::udp::RadarDataListener>,
          std::unique_ptr<zadar::udp::ImuDataListener>>>
  try_reserve_pair(
      std::uint16_t data_port,
      std::uint16_t imu_port,
      bool allow_port_in_use_scan = true) {
    try {
      auto radar_reservation = zadar::webapi::reserve_udp_port(bind_address_, data_port);
      auto imu_reservation = zadar::webapi::reserve_udp_port(bind_address_, imu_port);
      auto radar_listener = make_radar_listener(data_port);
      auto imu_listener = make_imu_listener(imu_port);
      radar_reservation.close();
      imu_reservation.close();
      radar_listener->open();
      imu_listener->open();
      return std::make_optional(std::make_tuple(
          data_port,
          imu_port,
          std::move(radar_listener),
          std::move(imu_listener)));
    } catch (const zadar::webapi::DriverControlError& error) {
      if (allow_port_in_use_scan && error.errnum() == EADDRINUSE) {
        return std::nullopt;
      }
      throw;
    } catch (const std::exception& error) {
      throw zadar::webapi::DriverControlError(
          "Unable to bind managed UDP listeners on " + bind_address_ + ":" +
          std::to_string(data_port) + " and " + bind_address_ + ":" +
          std::to_string(imu_port) + ": " + error.what());
    }
  }

  void log_launch_configuration() {
    if (managed_mode_) {
      const auto mode_text =
          running_mode_ >= 0 ? std::to_string(running_mode_) : std::string("not started");
      if (radar_stream_enabled_ && imu_stream_enabled_) {
        ROS_INFO(
            "Managed sensor %s configured for udp://%s:%u (radar) and udp://%s:%u (imu); listening on udp://%s:%u and udp://%s:%u; running mode: %s",
            sensor_hostname_.c_str(),
            destination_ip_.c_str(),
            static_cast<unsigned int>(data_port_),
            destination_ip_.c_str(),
            static_cast<unsigned int>(imu_port_),
            bind_address_.c_str(),
            static_cast<unsigned int>(data_port_),
            bind_address_.c_str(),
            static_cast<unsigned int>(imu_port_),
            mode_text.c_str());
      } else if (radar_stream_enabled_) {
        ROS_INFO(
            "Managed sensor %s configured for udp://%s:%u (radar); listening on udp://%s:%u; running mode: %s",
            sensor_hostname_.c_str(),
            destination_ip_.c_str(),
            static_cast<unsigned int>(data_port_),
            bind_address_.c_str(),
            static_cast<unsigned int>(data_port_),
            mode_text.c_str());
      } else if (imu_stream_enabled_) {
        ROS_INFO(
            "Managed sensor %s configured for udp://%s:%u (imu); listening on udp://%s:%u; running mode: %s",
            sensor_hostname_.c_str(),
            destination_ip_.c_str(),
            static_cast<unsigned int>(imu_port_),
            bind_address_.c_str(),
            static_cast<unsigned int>(imu_port_),
            mode_text.c_str());
      } else {
        ROS_INFO(
            "Managed sensor %s configured for destination IP %s; running mode: %s",
            sensor_hostname_.c_str(),
            destination_ip_.c_str(),
            mode_text.c_str());
      }
      return;
    }

    if (radar_stream_enabled_ && imu_stream_enabled_) {
      ROS_INFO(
          "Listening on udp://%s:%u (radar) and udp://%s:%u (imu)",
          bind_address_.c_str(),
          static_cast<unsigned int>(data_port_),
          bind_address_.c_str(),
          static_cast<unsigned int>(imu_port_));
    } else if (radar_stream_enabled_) {
      ROS_INFO(
          "Listening on udp://%s:%u (radar)",
          bind_address_.c_str(),
          static_cast<unsigned int>(data_port_));
    } else if (imu_stream_enabled_) {
      ROS_INFO(
          "Listening on udp://%s:%u (imu)",
          bind_address_.c_str(),
          static_cast<unsigned int>(imu_port_));
    }
  }

  void start_workers() {
    if (radar_listener_ != nullptr) {
      threads_.emplace_back([this]() { radar_loop(); });
    }
    if (imu_listener_ != nullptr) {
      threads_.emplace_back([this]() { imu_loop(); });
    }

    if (threads_.empty()) {
      ROS_WARN("No publishers are enabled; the driver is idle.");
    }
  }

  void log_status(
      std::map<int, std::size_t>& counters,
      int status_code,
      const char* label) {
    const auto count = ++counters[status_code];
    if (count <= 5U || count % 100U == 0U) {
      ROS_WARN("%s status %d received %zu time(s).", label, status_code, count);
    }
  }

  void radar_loop() {
    while (ros::ok() && !stop_requested_.load()) {
      try {
        const auto output = radar_listener_->read_frame();
        if (!output.has_value()) {
          continue;
        }
        if (output->status_code != zadar::udp::RadarStatusCode::kFine ||
            !output->data.has_value()) {
          log_status(
              radar_status_counts_,
              static_cast<int>(output->status_code),
              "Radar");
          continue;
        }

        const auto& payload = *output->data;
        const auto& radar_frame = payload.frame;
        const std::uint64_t fallback_timestamp_ns = frame_timestamp_ns(payload.timestamp);
        const std::uint64_t message_timestamp_ns =
            scan_timestamp_ns(radar_frame.radar_scan(), fallback_timestamp_ns);

        if (publish_scan_) {
          points_publisher_.publish(
              radar_scan_to_pointcloud2(
                  radar_frame.radar_scan(),
                  frame_id_,
                  message_timestamp_ns));
        }

        if (publish_clusters_) {
          clusters_publisher_.publish(
              clusters_to_msg(
                  radar_frame.clusters(),
                  frame_id_,
                  message_timestamp_ns));
        }

        if (publish_tracks_) {
          tracks_publisher_.publish(
              tracks_to_msg(
                  radar_frame.tracks(),
                  frame_id_,
                  message_timestamp_ns,
                  payload.frame_id));
        }

        if (publish_odometry_ && radar_frame.has_odometry()) {
          odometry_publisher_.publish(
              odometry_to_msg(
                  radar_frame.odometry(),
                  frame_id_,
                  message_timestamp_ns));
        }
      } catch (const std::exception& error) {
        if (!stop_requested_.load()) {
          ROS_ERROR("Radar listener stopped: %s", error.what());
        }
        break;
      }
    }
  }

  void imu_loop() {
    while (ros::ok() && !stop_requested_.load()) {
      try {
        const auto output = imu_listener_->read_packet();
        if (!output.has_value()) {
          continue;
        }
        if (output->status_code != zadar::udp::ImuStatusCode::kFine ||
            !output->data.has_value()) {
          log_status(
              imu_status_counts_,
              static_cast<int>(output->status_code),
              "IMU");
          continue;
        }

        if (publish_imu_) {
          imu_publisher_.publish(imu_to_msg(*output->data, frame_id_));
        }
      } catch (const std::exception& error) {
        if (!stop_requested_.load()) {
          ROS_ERROR("IMU listener stopped: %s", error.what());
        }
        break;
      }
    }
  }

  ros::NodeHandle nh_;
  ros::NodeHandle private_nh_;

  std::string configured_udp_bind_address_;
  std::string configured_legacy_bind_address_;
  std::string bind_address_;
  std::string sensor_hostname_;
  std::string host_ip_;
  std::string destination_ip_;
  std::string frame_id_;

  bool managed_mode_ = false;
  bool radar_stream_enabled_ = false;
  bool imu_stream_enabled_ = false;
  std::uint16_t requested_data_port_ = 0U;
  std::uint16_t requested_imu_port_ = 0U;
  std::uint16_t webapi_port_ = zadar::webapi::kDefaultWebApiPort;
  std::uint16_t data_port_ = 0U;
  std::uint16_t imu_port_ = 0U;
  std::size_t radar_socket_buffer_bytes_ = 0U;
  std::size_t imu_socket_buffer_bytes_ = 0U;
  std::size_t max_buffered_frames_ = 0U;
  int running_mode_ = -1;
  double frame_timeout_sec_ = 0.0;
  double socket_timeout_sec_ = 0.0;
  double webapi_timeout_sec_ = 5.0;

  bool publish_scan_ = true;
  bool publish_clusters_ = true;
  bool publish_tracks_ = true;
  bool publish_odometry_ = true;
  bool publish_imu_ = true;

  ros::Publisher points_publisher_;
  ros::Publisher clusters_publisher_;
  ros::Publisher tracks_publisher_;
  ros::Publisher odometry_publisher_;
  ros::Publisher imu_publisher_;

  std::unique_ptr<zadar::udp::RadarDataListener> radar_listener_;
  std::unique_ptr<zadar::udp::ImuDataListener> imu_listener_;

  std::vector<std::thread> threads_;
  std::atomic<bool> stop_requested_{false};
  std::map<int, std::size_t> radar_status_counts_;
  std::map<int, std::size_t> imu_status_counts_;
};

}  // namespace

int main(int argc, char** argv) {
  ros::init(argc, argv, "zadar_udp_driver");
  ros::AsyncSpinner spinner(1);
  spinner.start();

  auto node = std::make_unique<ZadarUdpDriverNode>();
  ros::waitForShutdown();
  node->stop();
  return 0;
}
