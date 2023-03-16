/* Copyright 2023 Man Group Operations Limited
 *
 * Use of this software is governed by the Business Source License 1.1 included in the file licenses/BSL.txt.
 *
 * As of the Change Date specified in that file, in accordance with the Business Source License, use of this software will be governed by the Apache License, version 2.0.
 */

#include <gtest/gtest.h> // googletest header file
#include <string>
#include <algorithm>
#include <fmt/format.h>

#include <arcticdb/util/random.h>
#include <arcticdb/util/timer.hpp>
#include <arcticdb/util/test/generators.hpp>
#include <arcticdb/stream/row_builder.hpp>
#include <arcticdb/stream/test/stream_test_common.hpp>
#include <arcticdb/stream/aggregator.hpp>
#include <arcticdb/pipeline/query.hpp>

using namespace arcticdb;
namespace as = arcticdb::stream;

#define GTEST_COUT std::cerr << "[          ] [ INFO ]"

std::string make_ast_name() {
    init_random(23);
    return fmt::format("{}_{}", "AST", random_int() % 0x100000 + 0x10000);
}

struct StubInfo {
    StubInfo(uint8_t *data, TypeDescriptor type) : ptr(data), type_(type) {}
    uint8_t *ptr;
    TypeDescriptor type_;
};

inline TypeDescriptor get_type_descriptor(StubInfo &info) {
    return info.type_;
}

template<typename T>
struct StubArray {
    StubArray(const std::vector<T> &data,
              std::vector<shape_t> &shapes,
              std::vector<stride_t>& strides,
              TypeDescriptor type) :
        type_(type),
        data_(data),
        shapes_(shapes),
        strides_(strides) {
    }

    StubArray(const T *data,
              size_t size,
              const std::vector<shape_t>& shapes,
              const std::vector<stride_t>& strides,
              TypeDescriptor type) :
        type_(type),
        data_(data, data + size),
        shapes_(shapes),
        strides_(strides) {
    }

    StubArray(const StubArray &other) = delete;
    StubArray &operator=(const StubArray &other) = delete;
    StubArray(StubArray &&other) = default;
    StubArray &operator=(StubArray &&other) = default;

    StubInfo request() { return StubInfo(reinterpret_cast<uint8_t *>(data_.data()), type_); }
    ssize_t ndim() { return 1; }
    ssize_t nbytes() const { return data_.size() * sizeof(T); }
    shape_t shape(int pos) { return shapes_[pos]; }
    shape_t *shape() { return shapes_.data(); }
    stride_t strides(int pos) { return strides_[pos]; }
    stride_t* strides() { return strides_.data(); }
    static size_t itemsize() { return sizeof(T); }
  private:
    TypeDescriptor type_;
    std::vector<T> data_;
    std::vector<shape_t> shapes_;
    std::vector<stride_t> strides_;
};

static const size_t NumChars = 16;

struct FixedStringStub {
    char chars_[NumChars];

    FixedStringStub() { chars_[0] = 0; }
    explicit FixedStringStub(const std::string &str) {
        memcpy(chars_, str.data(), std::min(str.size(), NumChars));
    }
    FixedStringStub(FixedStringStub &&that) {
        memcpy(chars_, that.chars_, NumChars);
    }
};

TEST(IngestionStress, ScalarInt) {
    const int64_t NumColumns = 20;
    const int64_t NumRows = 10000;
    const uint64_t SegmentPolicyRows = 1000;

    std::vector<FieldDescriptor> columns;
    for (auto i = 0; i < NumColumns; ++i)
        columns.push_back(FieldDescriptor(scalar_field_proto(DataType::UINT64, "uint64")));

    const auto index = as::TimeseriesIndex::default_index();
    as::FixedSchema schema{
        index.create_stream_descriptor(123, fields_proto_from_range(columns)), index
    };

    SegmentsSink sink;
    as::FixedTimestampAggregator agg(std::move(schema), [&](SegmentInMemory &&mem) {
        sink.segments_.push_back(std::move(mem));
    }, as::RowCountSegmentPolicy{SegmentPolicyRows});

    std::string timer_name("ingestion_stress");
    interval_timer timer(timer_name);
    size_t x = 0;
    for (auto i = 0; i < NumRows; ++i) {
        agg.start_row(timestamp{i})([&](auto &rb) {
            for (timestamp j = 1u; j <= timestamp(NumColumns); ++j)
                rb.set_scalar(j, uint64_t(i + j));
        });
    }
    timer.stop_timer(timer_name);
    GTEST_COUT << x << " " << timer.display_all() << std::endl;
}

TEST(IngestionStress, ScalarIntAppend) {
    using namespace arcticdb;
    const uint64_t NumColumns = 1;
    const uint64_t NumRows = 2;
    const uint64_t SegmentPolicyRows = 1000;

    StreamId symbol{"stable"};
    std::string lib_name("test.scalar_int_append");
    auto version_store = test_store(lib_name);
    std::vector<SegmentToInputFrameAdapter> data;
    // generate vals
    std::vector<FieldDescriptor> columns;
    for (timestamp i = 0; i < timestamp(NumColumns); ++i) {
        columns.push_back(FieldDescriptor(scalar_field_proto(DataType::UINT64, fmt::format("col_{}", i))));
    }

    const auto index = as::TimeseriesIndex::default_index();
    auto desc = index.create_stream_descriptor(symbol, {});
    as::DynamicSchema schema{desc, index};

    SegmentsSink sink;
    as::DynamicTimestampAggregator agg(std::move(schema), [&](SegmentInMemory &&mem) {
        sink.segments_.push_back(std::move(mem));
    }, as::RowCountSegmentPolicy{SegmentPolicyRows});


    std::string timer_name("ingestion_stress");
    interval_timer timer(timer_name);
    size_t x = 0;
    for (timestamp i = 0; i < timestamp(NumRows); ++i) {
        agg.start_row(timestamp{i})([&](auto &rb) {
            for (timestamp j = 1u; j <= timestamp(NumColumns); ++j)
                rb.set_scalar_by_name(columns[j-1].name(), uint64_t(i + j), columns[j-1].type_desc());
        });
    }
    timer.stop_timer(timer_name);
    GTEST_COUT << x << " " << timer.display_all() << std::endl;


    std::vector<FieldDescriptor> columns_second;
    for (auto i = 0; i < 2; ++i) {
        columns_second.emplace_back(FieldDescriptor(scalar_field_proto(DataType::UINT64, fmt::format("col_{}", i))));
    }

    auto new_descriptor = index.create_stream_descriptor(symbol, fields_proto_from_range(columns_second));

    for (timestamp i = 0u; i < timestamp(NumRows); ++i) {
        agg.start_row(timestamp(i + NumRows))([&](auto &rb) {
            for (uint64_t j = 1u; j <= 2; ++j)
                rb.set_scalar_by_name(columns_second[j-1].name(), uint64_t(i + j), columns_second[j-1].type_desc());
        });
    }
    GTEST_COUT << " 2 done";

    agg.commit();

    for(auto &seg : sink.segments_) {
        arcticdb::stream::append_incomplete_segment(version_store->_test_get_store(), symbol, std::move(seg));
    }

    using namespace arcticdb::pipelines;

    auto ro = ReadOptions{};
    ro.allow_sparse_ = true;
    ro.set_dynamic_schema(true);
    ro.set_incompletes(true);
    ReadQuery read_query;
    read_query.row_filter = universal_range();
    auto read_result = version_store->read_dataframe_version(symbol, VersionQuery{}, read_query, ro);
    GTEST_COUT << "columns in res: " << read_result.frame_data.index_columns().size();
}

TEST(IngestionStress, ScalarIntDynamicSchema) {
    const uint64_t NumColumnsFirstWrite = 5;
    const uint64_t NumColumnsSecondWrite = 10;
    const int64_t NumRows = 10;
    const uint64_t SegmentPolicyRows = 100;
    StreamId symbol{"blah"};

    std::string lib_name("wdealtry.tick_ingestion4");
    auto version_store = test_store(lib_name);
    std::vector<SegmentToInputFrameAdapter> data;

    // generate vals
    std::vector<FieldDescriptor> columns_first;
    std::vector<FieldDescriptor::Proto> columns_second;
    for (timestamp i = 0; i < timestamp(NumColumnsFirstWrite); ++i) {
        columns_first.emplace_back(scalar_field_proto(DataType::UINT64,  fmt::format("col_{}", i)));
    }

    const auto index = as::TimeseriesIndex::default_index();
    as::DynamicSchema schema{index.create_stream_descriptor(symbol, {}), index};

    SegmentsSink sink;
    as::DynamicTimestampAggregator agg(std::move(schema), [&](SegmentInMemory &&mem) {
        sink.segments_.push_back(std::move(mem));
    }, as::RowCountSegmentPolicy{SegmentPolicyRows});

    std::string timer_name("ingestion_stress");
    interval_timer timer(timer_name);
    for (timestamp i = 0; i < timestamp(NumRows); ++i) {
        agg.start_row(timestamp{i})([&](auto &rb) {
            for (uint64_t j = 1u; j < NumColumnsFirstWrite; ++j)
                rb.set_scalar_by_name(columns_first[j-1].name(), uint64_t(i + j), columns_first[j-1].type_desc());
        });
    }
    timer.stop_timer(timer_name);
    GTEST_COUT << " 1 done";

    // Now try and write rows with more columns
    for (timestamp i = 0; i < timestamp(NumColumnsSecondWrite); ++i) {
        columns_second.emplace_back(scalar_field_proto(DataType::UINT64,  fmt::format("col_{}", i)));
    }
    auto new_descriptor = index.create_stream_descriptor(symbol, columns_second);

    // Now write again.

    for (timestamp i = 0; i < NumRows; ++i) {
        agg.start_row(timestamp{i + NumRows})([&](auto &rb) {
            for (uint64_t j = 1u; j < NumColumnsSecondWrite; ++j)
                rb.set_scalar_by_name(columns_second[j-1].name(), uint64_t(i + j), columns_second[j-1].type_desc());
        });
    }
    GTEST_COUT << " 2 done";


    // now write 5 columns
    for (auto i = 0u; i < NumRows; ++i) {
        agg.start_row(timestamp{i + NumRows * 2})([&](auto &rb) {
            for (uint64_t j = 1u; j < NumColumnsFirstWrite; ++j)
                rb.set_scalar_by_name(columns_first[j].name(), uint64_t(i + j), columns_first[j].type_desc());
        });
    }
    GTEST_COUT << " 3 done";

    // now write 10
    for (auto i = 0u; i < NumRows; ++i) {
        agg.start_row(timestamp{i + NumRows * 3})([&](auto &rb) {
            for (uint64_t j = 1u; j < NumColumnsSecondWrite; ++j)
                rb.set_scalar_by_name(columns_second[j].name(), uint64_t(i + j), columns_second[j].type_desc());
        });
    }


    agg.commit();


    for(auto &seg : sink.segments_) {
        log::version().info("Writing to symbol: {}", symbol);
        arcticdb::stream::append_incomplete_segment(version_store->_test_get_store(), symbol, std::move(seg));
    }

    using namespace arcticdb::pipelines;

    ReadOptions read_options;
    read_options.set_dynamic_schema(true);
    read_options.set_allow_sparse(true);
    read_options.set_incompletes(true);
    ReadQuery read_query;
    read_query.row_filter = universal_range();
    auto read_result = version_store->read_dataframe_internal(symbol, read_query, read_options);
}

TEST(IngestionStress, DynamicSchemaWithStrings) {
    const uint64_t NumRows = 10;
    const uint64_t SegmentPolicyRows = 100;
    StreamId symbol{"blah_string"};

    std::string lib_name("wdealtry.tick_ingestion_3");
    auto version_store = test_store(lib_name);
    std::vector<SegmentToInputFrameAdapter> data;

    const auto index = as::TimeseriesIndex::default_index();
    as::DynamicSchema schema{
           index.create_stream_descriptor(symbol, {
                    scalar_field_proto(DataType::INT64, "INT64"),
                    scalar_field_proto(DataType::ASCII_FIXED64, "ASCII"),
                    }), index
    };

    SegmentsSink sink;
    as::DynamicTimestampAggregator agg(std::move(schema), [&](SegmentInMemory &&mem) {
        sink.segments_.push_back(std::move(mem));
    }, as::RowCountSegmentPolicy{SegmentPolicyRows});

    std::string timer_name("ingestion_stress");
    interval_timer timer(timer_name);

    for (auto i = 0u; i < NumRows; ++i) {
        agg.start_row(timestamp{i})([&](auto &rb) {
            rb.set_scalar_by_name("INT64", uint64_t(i), make_scalar_type(DataType::INT64));
            auto val = fmt::format("hi_{}", i);
            rb.set_scalar_by_name("ASCII", std::string_view{val}, make_scalar_type(DataType::ASCII_FIXED64));
        });
    }
    timer.stop_timer(timer_name);
    GTEST_COUT << " 1 done";

    agg.commit();

    for(auto &seg : sink.segments_) {
        log::version().info("Writing to symbol: {}", symbol);
        arcticdb::stream::append_incomplete_segment(version_store->_test_get_store(), symbol, std::move(seg));
    }

    using namespace arcticdb::pipelines;

    ReadOptions read_options;
    read_options.set_dynamic_schema(true);
    read_options.set_allow_sparse(true);
    read_options.set_incompletes(true);
    ReadQuery read_query;
    read_query.row_filter = universal_range();
    auto read_result = version_store->read_dataframe_version(symbol, VersionQuery{}, read_query, read_options);
    log::version().info("result columns: {}", read_result.frame_data.names());
}