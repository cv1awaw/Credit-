# Use a base image with essential build tools
FROM ubuntu:22.04

# Install OS packages needed to build TgBot & your code
RUN apt-get update && apt-get install -y \
    g++ \
    cmake \
    libssl-dev \
    libboost-system-dev \
    libboost-program-options-dev \
    libboost-iostreams-dev \
    libcurl4-openssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Build TgBot from source
WORKDIR /tmp
RUN git clone --recursive https://github.com/reo7sp/tgbot-cpp.git
WORKDIR /tmp/tgbot-cpp
RUN mkdir build && cd build && cmake .. && make -j4 && make install

# Copy your bot source into /app
WORKDIR /app
COPY . /app

# Build your bot with CMake
RUN mkdir build && cd build && cmake .. && make -j4

# Set environment variable BOT_TOKEN at runtime (Railway does this, or you do it manually)
ENV BOT_TOKEN=""

# By default, run the compiled bot
CMD ["./build/MyTelegramBot"]
