#pragma once

#include <array>
#include <cstdint>
#include <vector>

namespace zadar::udp {

class CRC64Ecma182 {
 public:
  CRC64Ecma182() : crc_(0xFFFFFFFFFFFFFFFFULL) {}

  void update(const std::uint8_t* data, std::size_t size) {
    for (std::size_t i = 0; i < size; ++i) {
      const auto table_index = static_cast<std::uint8_t>((crc_ ^ data[i]) & 0xFFU);
      crc_ = (table()[table_index] ^ (crc_ >> 8U)) & 0xFFFFFFFFFFFFFFFFULL;
    }
  }

  void update(const std::vector<std::uint8_t>& data) {
    update(data.data(), data.size());
  }

  [[nodiscard]] std::uint64_t digest() const {
    return crc_ ^ 0xFFFFFFFFFFFFFFFFULL;
  }

 private:
  static const std::array<std::uint64_t, 256>& table() {
    static const auto lookup = [] {
      std::array<std::uint64_t, 256> values{};
      constexpr std::uint64_t reversed_poly = 0xC96C5795D7870F42ULL;
      for (std::size_t value = 0; value < values.size(); ++value) {
        std::uint64_t crc = value;
        for (int bit = 0; bit < 8; ++bit) {
          if ((crc & 1ULL) != 0ULL) {
            crc = (crc >> 1U) ^ reversed_poly;
          } else {
            crc >>= 1U;
          }
        }
        values[value] = crc & 0xFFFFFFFFFFFFFFFFULL;
      }
      return values;
    }();
    return lookup;
  }

  std::uint64_t crc_;
};

}  // namespace zadar::udp
