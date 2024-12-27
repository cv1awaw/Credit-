find_package(Boost REQUIRED COMPONENTS system)
find_package(OpenSSL REQUIRED)
find_package(TgBot REQUIRED)

add_executable(MyTelegramBot main.cpp)

target_link_libraries(MyTelegramBot
    PRIVATE
    Boost::system
    OpenSSL::SSL
    OpenSSL::Crypto
    TgBot::TgBot
)
