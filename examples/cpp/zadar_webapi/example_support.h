#pragma once

#include <cstdlib>
#include <iostream>
#include <string>

#include "zadar/webapi/client.h"

namespace zadar::webapi::examples {

inline void print_response(const std::string& title, const Response& response) {
  std::cout << "\n=== " << title << " ===\n";
  std::cout << "status_code=" << response.status_code
            << " success=" << (response.success ? "true" : "false") << '\n';
  if (!response.error.empty()) {
    std::cout << "error=" << response.error << '\n';
  } else {
    std::cout << response.body << '\n';
  }
}

inline std::string require_option(int argc, char** argv, const std::string& option) {
  for (int i = 1; i + 1 < argc; ++i) {
    if (argv[i] == option) {
      return argv[i + 1];
    }
  }
  std::cerr << "Missing required option: " << option << '\n';
  std::exit(1);
}

inline std::string optional_option(
    int argc,
    char** argv,
    const std::string& option,
    const std::string& default_value) {
  for (int i = 1; i + 1 < argc; ++i) {
    if (argv[i] == option) {
      return argv[i + 1];
    }
  }
  return default_value;
}

inline bool has_flag(int argc, char** argv, const std::string& flag) {
  for (int i = 1; i < argc; ++i) {
    if (argv[i] == flag) {
      return true;
    }
  }
  return false;
}

inline int optional_int_option(
    int argc,
    char** argv,
    const std::string& option,
    int default_value) {
  return std::stoi(optional_option(argc, argv, option, std::to_string(default_value)));
}

}  // namespace zadar::webapi::examples
