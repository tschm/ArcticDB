#include <gtest/gtest.h>

class MyTests : public ::testing::Test{
};

TEST_F(MyTests, simple )
{
    EXPECT_EQ(1, 3-2 );
}

