# Use an official Ubuntu base image
FROM ubuntu:22.04

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install necessary system packages
#    - build-essential, cmake for building C++ code
#    - libboost-all-dev for Boost::system, etc.
#    - libssl-dev, libcurl4-openssl-dev for SSL/TLS
#    - wget, git for fetching tgbot-cpp
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        cmake \
        libboost-all-dev \
        libssl-dev \
        libcurl4-openssl-dev \
        wget git

# 2. Download & build tgbot-cpp library
RUN git clone https://github.com/reo7sp/tgbot-cpp.git /opt/tgbot-cpp
WORKDIR /opt/tgbot-cpp
RUN mkdir build && cd build && cmake .. && make -j4 && make install

# 3. Copy your bot's source code into the container
WORKDIR /app
COPY . /app

# 4. Build your bot using CMake
RUN mkdir build && cd build && cmake .. && make -j4

# 5. Define the default command to run your bot
#    Railway will run this command after building
CMD ["./build/MyTelegramBot"]
