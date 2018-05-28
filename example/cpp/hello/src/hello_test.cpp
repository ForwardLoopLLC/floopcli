#include "hello.h"
#include <gtest/gtest.h>

TEST(helloTest, test){
    // passes if hello returns exit code 0
    EXPECT_EQ(0, hello());
}
