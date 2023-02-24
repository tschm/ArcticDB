find_package(Folly REQUIRED)
find_package(GLog REQUIRED)

add_executable(folly_format main.cpp)
#target_link_libraries(folly_format PUBLIC Folly::folly_deps Folly::folly glog::glog -static-libgcc -static-libstdc++)
target_link_libraries(folly_format PRIVATE -static-libgcc -static-libstdc++ Folly::folly glog::glog)

