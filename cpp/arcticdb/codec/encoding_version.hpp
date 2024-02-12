#pragma once

#include <cstdint>

namespace arcticdb {

enum class EncodingVersion : uint16_t {
    V1 = 0,
    V2 = 1,
    COUNT = 2
};

} //namespace arcticdb