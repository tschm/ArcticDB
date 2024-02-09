#pragma once

#include <arcticdb/entity/protobufs.hpp>
#include <arcticdb/codec/encoded_field.hpp>
#include <arcticdb/util/preconditions.hpp>

namespace arcticdb {

size_t calc_encoded_field_buffer_size(const arcticdb::proto::encoding::EncodedField& field) {
    size_t bytes = EncodedField::Size;
    util::check(field.has_ndarray(), "Only ndarray translations supported");
    const auto& ndarray = field.ndarray();
    util::check(ndarray.shapes_size() < 2, "Unexpected number of shapes in proto translation: {}", ndarray.shapes_size());
    bytes += sizeof(EncodedBlock) * ndarray.shapes_size();
    bytes += sizeof(EncodedBlock) * ndarray.values_size();
    return bytes;
}

void block_from_proto(const arcticdb::proto::encoding::Block& input, EncodedBlock& output, bool is_shape) {
    output.set_in_bytes(input.in_bytes());
    output.set_out_bytes(input.out_bytes());
    output.set_hash(input.hash());
    output.set_encoder_version(input.encoder_version());
    output.is_shape_ = is_shape;
    switch (input.codec().codec_case()) {
        case arcticdb::proto::encoding::VariantCodec::kZstd: {
            const auto &zstd_in = input.codec().zstd();
            auto *zstd_out = output.mutable_codec()->mutable_zstd();
            break;
        }
        case arcticdb::proto::encoding::VariantCodec::kLz4: {
            const auto &lz4_in = input.codec().zstd();
            auto *lz4_out = output.mutable_codec()->mutable_lz4();
            break;
        }
        case arcticdb::proto::encoding::VariantCodec::kPassthrough : {
            const auto &passthrough_in = input.codec().passthrough();
            auto *passthrough_out = output.mutable_codec()->mutable_passthrough();
            break;
        }
        default:
            util::raise_rte("Unrecognized_codec");
    }
}

void proto_from_block(const EncodedBlock& input, arcticdb::proto::encoding::Block& output) {
    output.set_in_bytes(input.in_bytes());
    output.set_out_bytes(input.out_bytes());
    output.set_hash(input.hash());
    output.set_encoder_version(input.encoder_version());

    switch (input.codec().codec_case()) {
    case arcticdb::proto::encoding::VariantCodec::kZstd: {
        const auto &zstd_in = input.codec().zstd();
        auto *zstd_out = output.mutable_codec()->mutable_zstd();
        break;
    }
    case arcticdb::proto::encoding::VariantCodec::kLz4: {
        const auto &lz4_in = input.codec().zstd();
        auto *lz4_out = output.mutable_codec()->mutable_lz4();
        break;
    }
    case arcticdb::proto::encoding::VariantCodec::kPassthrough: {
        const auto &passthrough_in = input.codec().passthrough();
        auto *passthrough_out = output.mutable_codec()->mutable_passthrough();
        break;
    }
    default:
        util::raise_rte("Unrecognized_codec");
    }
}

void encoded_field_from_proto(const arcticdb::proto::encoding::EncodedField& input, EncodedField& output) {
    util::check(input.has_ndarray(), "Only ndarray fields supported for v1 encoding");
    const auto& input_ndarray = input.ndarray();
    auto* output_ndarray = output.mutable_ndarray();

    output_ndarray->set_items_count(input_ndarray.items_count());
    util::check(input_ndarray.shapes_size() < 2, "Unexpected number of shapes in proto translation");
    if(input_ndarray.shapes_size() == 1) {
        auto* shape_block = output_ndarray->add_shapes();
        block_from_proto(input_ndarray.shapes(0), *shape_block, true);
    }

    for(auto i = 0; i < input_ndarray.values_size(); ++i) {
        auto* value_block = output_ndarray->add_values();
        block_from_proto(input_ndarray.values(i), *value_block, false);
    }
}

void proto_from_encoded_field(EncodedField& input, arcticdb::proto::encoding::EncodedField& output) {
    util::check(input.has_ndarray(), "Only ndarray fields supported for v1 encoding");
    const auto& input_ndarray = input.ndarray();
    auto* output_ndarray = output.mutable_ndarray();

    output_ndarray->set_items_count(input_ndarray.items_count());
    util::check(input_ndarray.shapes_size() < 2, "Unexpected number of shapes in proto translation");
    if(input_ndarray.shapes_size() == 1) {
        auto* shape_block = output_ndarray->add_shapes();
        proto_from_block(input_ndarray.shapes(0), *shape_block);
    }

    for(auto i = 0; i < input_ndarray.values_size(); ++i) {
        auto* value_block = output_ndarray->add_values();
        proto_from_block(input_ndarray.values(i), *value_block);
    }
}

} //namespace arcticdb