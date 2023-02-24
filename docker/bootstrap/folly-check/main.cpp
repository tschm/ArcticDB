#include <folly/Format.h>
#include <iostream>


int main(int argc,char**argv){
    std::cout<<folly::format("Hello {}", "World")<<std::endl;
}
