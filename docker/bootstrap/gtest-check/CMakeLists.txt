find_package(GTest REQUIRED)
enable_testing()

add_executable(unit_tests unit_tests.cc)

target_link_libraries(unit_tests gtest gmock gtest_main Threads::Threads -static-libgcc -static-libstdc++)

add_test(test_all unit_tests)
