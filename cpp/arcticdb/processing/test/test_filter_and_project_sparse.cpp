/* Copyright 2023 Man Group Operations Limited
 *
 * Use of this software is governed by the Business Source License 1.1 included in the file licenses/BSL.txt.
 *
 * As of the Change Date specified in that file, in accordance with the Business Source License, use of this software will be governed by the Apache License, version 2.0.
 */

#include <gtest/gtest.h>
#include <arcticdb/processing/processing_unit.hpp>
#include <arcticdb/util/test/generators.hpp>

TEST(ProjectSparse, UnaryArithmetic) {
    using namespace arcticdb;

    const std::string input_column_name{"sparse_floats_1"};
    const std::string output_column{"NEG"};

    auto expression_node = std::make_shared<ExpressionNode>(ColumnName(input_column_name), OperationType::NEG);
    auto expression_context = std::make_shared<ExpressionContext>();
    expression_context->add_expression_node(output_column, expression_node);
    expression_context->root_node_name_ = ExpressionName(output_column);

    auto input_segment = generate_filter_and_project_testing_sparse_segment();
    auto input_column = input_segment.column_ptr(input_segment.column_index(input_column_name).value());

    auto proc_unit = ProcessingUnit(std::move(input_segment));
    proc_unit.set_expression_context(expression_context);

    auto variant_data = proc_unit.get(expression_context->root_node_name_);

    ASSERT_TRUE(std::holds_alternative<ColumnWithStrings>(variant_data));
    auto& projected_column = *std::get<ColumnWithStrings>(variant_data).column_;

    ASSERT_EQ(input_column->last_row(), projected_column.last_row());
    ASSERT_EQ(input_column->row_count(), projected_column.row_count());
    ASSERT_EQ(input_column->opt_sparse_map(), projected_column.opt_sparse_map());

    for (auto idx=0; idx< input_column->row_count(); idx++) {
        ASSERT_FLOAT_EQ(input_column->reference_at<double>(idx), -projected_column.reference_at<double>(idx));
    }
}

//TEST(FilterSparse, NOTNULL) {
//    using namespace arcticdb;
//    auto component_manager = std::make_shared<ComponentManager>();
//
//    const std::string input_column_name{"sparse_floats_1"};
//    const std::string root_node_name{"sparse_floats_1 notnull"};
//
//    auto expression_node = std::make_shared<ExpressionNode>(ColumnName(input_column_name), OperationType::NOTNULL);
//    ExpressionContext expression_context;
//    expression_context.add_expression_node(root_node_name, expression_node);
//    expression_context.root_node_name_ = ExpressionName(root_node_name);
//
//    FilterClause filter({}, expression_context, std::nullopt);
//    filter.set_component_manager(component_manager);
//
//    auto input_segment = generate_filter_and_project_testing_sparse_segment();
//    auto original_segment = input_segment.clone();
//    auto input_column = input_segment.column_ptr(input_segment.column_index(input_column_name).value());
//
//    auto proc_unit = ProcessingUnit(std::move(input_segment));
//    auto entity_ids = Composite<EntityIds>(push_entities(component_manager, std::move(proc_unit)));
//
//    auto filtered = gather_entities(component_manager, filter.process(std::move(entity_ids))).as_range();
//    ASSERT_EQ(1, filtered.size());
//    ASSERT_TRUE(filtered[0].segments_.has_value());
//    auto segments = filtered[0].segments_.value();
//    ASSERT_EQ(1, segments.size());
//    auto segment = *segments[0];
//    ASSERT_EQ(segment.row_count(), 3);
//}

TEST(ProjectSparse, BinaryArithmeticColVal) {
    using namespace arcticdb;

    const std::string input_column_name{"sparse_floats_1"};
    const std::string value_name{"ten"};
    const std::string output_column{"MUL"};

    auto expression_node = std::make_shared<ExpressionNode>(ColumnName(input_column_name), ValueName(value_name), OperationType::MUL);
    auto expression_context = std::make_shared<ExpressionContext>();
    expression_context->add_expression_node(output_column, expression_node);
    expression_context->add_value(value_name, std::make_shared<Value>(double(10.0), DataType::FLOAT64));
    expression_context->root_node_name_ = ExpressionName(output_column);

    auto input_segment = generate_filter_and_project_testing_sparse_segment();
    auto input_column = input_segment.column_ptr(input_segment.column_index(input_column_name).value());

    auto proc_unit = ProcessingUnit(std::move(input_segment));
    proc_unit.set_expression_context(expression_context);

    auto variant_data = proc_unit.get(expression_context->root_node_name_);

    ASSERT_TRUE(std::holds_alternative<ColumnWithStrings>(variant_data));
    auto& projected_column = *std::get<ColumnWithStrings>(variant_data).column_;

    ASSERT_EQ(input_column->last_row(), projected_column.last_row());
    ASSERT_EQ(input_column->row_count(), projected_column.row_count());
    ASSERT_EQ(input_column->opt_sparse_map(), projected_column.opt_sparse_map());

    for (auto idx=0; idx< input_column->row_count(); idx++) {
        ASSERT_FLOAT_EQ(10.0 * input_column->reference_at<double>(idx), projected_column.reference_at<double>(idx));
    }
}

TEST(ProjectSparse, BinaryArithmeticSparseColSparseCol) {
    using namespace arcticdb;

    const std::string lhs_column_name{"sparse_floats_1"};
    const std::string rhs_column_name{"sparse_floats_2"};
    const std::string output_column{"MUL"};

    auto expression_node = std::make_shared<ExpressionNode>(ColumnName(lhs_column_name), ColumnName(rhs_column_name), OperationType::MUL);
    auto expression_context = std::make_shared<ExpressionContext>();
    expression_context->add_expression_node(output_column, expression_node);
    expression_context->root_node_name_ = ExpressionName(output_column);

    auto input_segment = generate_filter_and_project_testing_sparse_segment();
    auto lhs_input_column = input_segment.column_ptr(input_segment.column_index(lhs_column_name).value());
    auto rhs_input_column = input_segment.column_ptr(input_segment.column_index(rhs_column_name).value());

    auto proc_unit = ProcessingUnit(std::move(input_segment));
    proc_unit.set_expression_context(expression_context);

    auto variant_data = proc_unit.get(expression_context->root_node_name_);

    ASSERT_TRUE(std::holds_alternative<ColumnWithStrings>(variant_data));
    auto& projected_column = *std::get<ColumnWithStrings>(variant_data).column_;

    // sparse_floats_1 has fewer values than sparse_floats_2
    ASSERT_EQ(lhs_input_column->last_row(), projected_column.last_row());
    ASSERT_TRUE(projected_column.opt_sparse_map().has_value());
    ASSERT_EQ(*lhs_input_column->opt_sparse_map() & *rhs_input_column->opt_sparse_map(), *projected_column.opt_sparse_map());
    ASSERT_EQ(projected_column.row_count(), projected_column.opt_sparse_map()->count());

    for (auto idx = 0; idx <= projected_column.last_row(); idx++) {
        auto opt_left_value = lhs_input_column->scalar_at<double>(idx);
        auto opt_right_value = rhs_input_column->scalar_at<double>(idx);
        auto opt_projected_value = projected_column.scalar_at<double>(idx);
        if (opt_left_value.has_value() && opt_right_value.has_value()) {
            ASSERT_TRUE(opt_projected_value.has_value());
            if (std::isnan(*opt_left_value * *opt_right_value)) {
                ASSERT_TRUE(std::isnan(*opt_projected_value));
            } else {
                ASSERT_FLOAT_EQ(*opt_left_value * *opt_right_value, *projected_column.scalar_at<double>(idx));
            }
        } else {
            ASSERT_FALSE(projected_column.has_value_at(idx));
        }
    }
}

TEST(ProjectSparse, BinaryArithmeticDenseColDenseCol) {
    using namespace arcticdb;
    auto component_manager = std::make_shared<ComponentManager>();

    const std::string lhs_column_name{"dense_floats_1"};
    const std::string rhs_column_name{"dense_floats_2"};
    const std::string output_column{"MUL"};

    auto expression_node = std::make_shared<ExpressionNode>(ColumnName(lhs_column_name), ColumnName(rhs_column_name), OperationType::MUL);
    auto expression_context = std::make_shared<ExpressionContext>();
    expression_context->add_expression_node(output_column, expression_node);
    expression_context->root_node_name_ = ExpressionName(output_column);

    auto input_segment = generate_filter_and_project_testing_sparse_segment();
    auto lhs_input_column = input_segment.column_ptr(input_segment.column_index(lhs_column_name).value());
    auto rhs_input_column = input_segment.column_ptr(input_segment.column_index(rhs_column_name).value());

    auto proc_unit = ProcessingUnit(std::move(input_segment));
    proc_unit.set_expression_context(expression_context);

    auto variant_data = proc_unit.get(expression_context->root_node_name_);

    ASSERT_TRUE(std::holds_alternative<ColumnWithStrings>(variant_data));
    auto& projected_column = *std::get<ColumnWithStrings>(variant_data).column_;

    // dense_floats_1 has fewer values than dense_floats_2
    ASSERT_EQ(lhs_input_column->last_row(), projected_column.last_row());
    ASSERT_EQ(lhs_input_column->row_count(), projected_column.row_count());
    ASSERT_FALSE(projected_column.opt_sparse_map().has_value());

    for (auto idx=0; idx< lhs_input_column->last_row(); idx++) {
        ASSERT_FLOAT_EQ(lhs_input_column->reference_at<double>(idx) * rhs_input_column->reference_at<double>(idx),
                        projected_column.reference_at<double>(idx));
    }
}

TEST(ProjectSparse, BinaryArithmeticSparseColShorterThanDenseCol) {
    using namespace arcticdb;

    const std::string lhs_column_name{"sparse_floats_1"};
    const std::string rhs_column_name{"dense_floats_1"};
    const std::string output_column{"MUL"};

    auto expression_node = std::make_shared<ExpressionNode>(ColumnName(lhs_column_name), ColumnName(rhs_column_name), OperationType::MUL);
    auto expression_context = std::make_shared<ExpressionContext>();
    expression_context->add_expression_node(output_column, expression_node);
    expression_context->root_node_name_ = ExpressionName(output_column);

    auto input_segment = generate_filter_and_project_testing_sparse_segment();
    auto lhs_input_column = input_segment.column_ptr(input_segment.column_index(lhs_column_name).value());
    auto rhs_input_column = input_segment.column_ptr(input_segment.column_index(rhs_column_name).value());

    auto proc_unit = ProcessingUnit(std::move(input_segment));
    proc_unit.set_expression_context(expression_context);

    auto variant_data = proc_unit.get(expression_context->root_node_name_);

    ASSERT_TRUE(std::holds_alternative<ColumnWithStrings>(variant_data));
    auto& projected_column = *std::get<ColumnWithStrings>(variant_data).column_;

    // sparse_floats_1 has fewer rows than dense_floats_1
    ASSERT_EQ(lhs_input_column->last_row(), projected_column.last_row());
    ASSERT_TRUE(projected_column.opt_sparse_map().has_value());
    ASSERT_EQ(*lhs_input_column->opt_sparse_map(), *projected_column.opt_sparse_map());
    ASSERT_EQ(projected_column.row_count(), projected_column.opt_sparse_map()->count());

    for (auto idx = 0; idx <= projected_column.last_row(); idx++) {
        auto opt_left_value = lhs_input_column->scalar_at<double>(idx);
        auto opt_right_value = rhs_input_column->scalar_at<double>(idx);
        auto opt_projected_value = projected_column.scalar_at<double>(idx);
        if (opt_left_value.has_value() && opt_right_value.has_value()) {
            ASSERT_TRUE(opt_projected_value.has_value());
            if (std::isnan(*opt_left_value * *opt_right_value)) {
                ASSERT_TRUE(std::isnan(*opt_projected_value));
            } else {
                ASSERT_FLOAT_EQ(*opt_left_value * *opt_right_value, *projected_column.scalar_at<double>(idx));
            }
        } else {
            ASSERT_FALSE(projected_column.has_value_at(idx));
        }
    }
}

TEST(ProjectSparse, BinaryArithmeticSparseColLongerThanDenseCol) {
    using namespace arcticdb;

    const std::string lhs_column_name{"dense_floats_1"};
    const std::string rhs_column_name{"sparse_floats_2"};
    const std::string output_column{"MUL"};

    auto expression_node = std::make_shared<ExpressionNode>(ColumnName(lhs_column_name), ColumnName(rhs_column_name), OperationType::MUL);
    auto expression_context = std::make_shared<ExpressionContext>();
    expression_context->add_expression_node(output_column, expression_node);
    expression_context->root_node_name_ = ExpressionName(output_column);

    auto input_segment = generate_filter_and_project_testing_sparse_segment();
    auto lhs_input_column = input_segment.column_ptr(input_segment.column_index(lhs_column_name).value());
    auto rhs_input_column = input_segment.column_ptr(input_segment.column_index(rhs_column_name).value());

    auto proc_unit = ProcessingUnit(std::move(input_segment));
    proc_unit.set_expression_context(expression_context);

    auto variant_data = proc_unit.get(expression_context->root_node_name_);

    ASSERT_TRUE(std::holds_alternative<ColumnWithStrings>(variant_data));
    auto& projected_column = *std::get<ColumnWithStrings>(variant_data).column_;

    // dense_floats_1 has fewer rows than sparse_floats_2
    ASSERT_EQ(lhs_input_column->last_row(), projected_column.last_row());
    ASSERT_TRUE(projected_column.opt_sparse_map().has_value());
    for (size_t idx = 0; idx < projected_column.opt_sparse_map()->size(); idx++) {
        ASSERT_EQ(rhs_input_column->opt_sparse_map()->get_bit(idx), projected_column.opt_sparse_map()->get_bit(idx));
    }
    ASSERT_EQ(projected_column.row_count(), projected_column.opt_sparse_map()->count());

    for (auto idx = 0; idx <= projected_column.last_row(); idx++) {
        auto opt_left_value = lhs_input_column->scalar_at<double>(idx);
        auto opt_right_value = rhs_input_column->scalar_at<double>(idx);
        auto opt_projected_value = projected_column.scalar_at<double>(idx);
        if (opt_left_value.has_value() && opt_right_value.has_value()) {
            ASSERT_TRUE(opt_projected_value.has_value());
            if (std::isnan(*opt_left_value * *opt_right_value)) {
                ASSERT_TRUE(std::isnan(*opt_projected_value));
            } else {
                ASSERT_FLOAT_EQ(*opt_left_value * *opt_right_value, *projected_column.scalar_at<double>(idx));
            }
        } else {
            ASSERT_FALSE(projected_column.has_value_at(idx));
        }
    }
}