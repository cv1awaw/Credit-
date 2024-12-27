FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-all-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    wget git

# ... clone/build tgbot-cpp or other libraries ...

WORKDIR /app
COPY . /app

RUN mkdir build && cd build && cmake .. && make -j4

CMD ["./build/MyTelegramBot"]
