cmake_minimum_required(VERSION 3.10)
project(MyTelegramBot)

set(CMAKE_CXX_STANDARD 17)

# If TgBot is installed system-wide, you can do:
find_package(TgBot REQUIRED)

# main.cpp is your bot's source
add_executable(MyTelegramBot main.cpp)

target_link_libraries(MyTelegramBot TgBot::TgBot)
