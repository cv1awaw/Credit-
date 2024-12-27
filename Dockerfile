FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    g++ \
    cmake \
    libssl-dev \
    libboost-system-dev \
    libboost-program-options-dev \
    libboost-iostreams-dev \
    libcurl4-openssl-dev \
    git \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Build TgBot from source
WORKDIR /tmp
RUN git clone --recursive https://github.com/reo7sp/tgbot-cpp.git
WORKDIR /tmp/tgbot-cpp
RUN mkdir build && cd build && cmake .. && make -j4 && make install

# Copy your bot source into /app
WORKDIR /app
COPY . /app

# Build your bot
RUN mkdir build && cd build && cmake .. && make -j4

# Set BOT_TOKEN at runtime (Railway can do this under "Variables")
ENV BOT_TOKEN=""
CMD ["./build/MyTelegramBot"]
