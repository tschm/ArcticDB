find_package(Boost 1.67.0 REQUIRED)
find_package(Boost 1.67.0 COMPONENTS system filesystem REQUIRED)

add_executable(bootstrap main.cpp)
target_link_libraries(bootstrap PUBLIC Boost::boost Boost::system Threads::Threads -static-libgcc -static-libstdc++)

