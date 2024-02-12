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

template <typename Input, typename Output>
void set_codec(Input& in, Output& out) {
    out.MergeFrom(in);
}

void block_from_proto(const arcticdb::proto::encoding::Block& input, EncodedBlock& output, bool is_shape) {
    output.set_in_bytes(input.in_bytes());
    output.set_out_bytes(input.out_bytes());
    output.set_hash(input.hash());
    output.set_encoder_version(input.encoder_version());
    output.is_shape_ = is_shape;
    switch (input.codec().codec_case()) {
        case arcticdb::proto::encoding::VariantCodec::kZstd: {
            set_codec(input.codec().zstd(), *output.mutable_codec()->mutable_zstd());
            break;
        }
        case arcticdb::proto::encoding::VariantCodec::kLz4: {
            set_codec(input.codec().lz4(), *output.mutable_codec()->mutable_lz4());
            break;
        }
        case arcticdb::proto::encoding::VariantCodec::kPassthrough : {
            set_codec(input.codec().lz4(), *output.mutable_codec()->mutable_lz4());
            break;
        }
        default:
            util::raise_rte("Unrecognized_codec");
    }
}

void set_lz4(const Lz4Codec& lz4_in, arcticdb::proto::encoding::VariantCodec::Lz4& lz4_out) {
    lz4_out.set_acceleration(lz4_in.acceleration_);
}


void set_zstd(const ZstdCodec& zstd_in, arcticdb::proto::encoding::VariantCodec::Zstd& zstd_out) {
    zstd_out.set_is_streaming(zstd_in.is_streaming_);
    zstd_out.set_level(zstd_in.level_);
}

void set_passthrough(const PassthroughCodec& passthrough_in, arcticdb::proto::encoding::VariantCodec::Passthrough& passthrough_out) {
    passthrough_out.set_mark(passthrough_in.unused_);
}

void proto_from_block(const EncodedBlock& input, arcticdb::proto::encoding::Block& output) {
    output.set_in_bytes(input.in_bytes());
    output.set_out_bytes(input.out_bytes());
    output.set_hash(input.hash());
    output.set_encoder_version(input.encoder_version());

    switch (input.codec().codec_case()) {
    case arcticdb::proto::encoding::VariantCodec::kZstd: {
        set_zstd(input.codec().zstd(), *output.mutable_codec()->mutable_zstd());
        break;
    }
    case arcticdb::proto::encoding::VariantCodec::kLz4: {
        set_lz4(input.codec().lz4(), *output.mutable_codec()->mutable_lz4());
        break;
    }
    case arcticdb::proto::encoding::VariantCodec::kPassthrough: {
        set_passthrough(input.codec().passthrough(), *output.mutable_codec()->mutable_passthrough());
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

void proto_from_encoded_field(const EncodedField& input, arcticdb::proto::encoding::EncodedField& output) {
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