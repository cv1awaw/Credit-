cmake_minimum_required(VERSION 3.10)
project(MyTelegramBot)

# Use C++17 (modify if you need a different version)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 1. Find the necessary libraries
find_package(Boost REQUIRED COMPONENTS system)  # For Boost::system
find_package(OpenSSL REQUIRED)
find_package(TgBot REQUIRED)                    # Provided by tgbot-cpp

# 2. Add the executable
add_executable(MyTelegramBot main.cpp)

# 3. Link libraries
target_link_libraries(MyTelegramBot
    PRIVATE
    Boost::system
    OpenSSL::SSL
    OpenSSL::Crypto
    TgBot::TgBot
)
