FROM ubuntu:22.04

WORKDIR app

RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install wget curl build-essential ffmpeg libsm6 libxext6 libgl1-mesa-glx \
    libfontconfig1 libxrender1 python-is-python3 libgl1 libgl1-mesa-dev  \
    '^libxcb.*-dev' libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev \
    libxkbcommon-dev libxkbcommon-x11-dev libxcb-xinerama0 -y

#RUN wget "https://repo.continuum.io/archive/Anaconda3-2023.03-Linux-x86_64.sh" -O "Anaconda-latest-Linux-x86_64.sh" && \
#    bash Anaconda-latest-Linux-x86_64.sh -b -p ~/anaconda3

COPY . .

RUN bash Anaconda-latest-Linux-x86_64.sh -b -p ~/anaconda3 && \
    ~/anaconda3/bin/conda init bash

#CMD ["app"]

ENTRYPOINT ["make", "app"]

# xhost
# xhost +local:docker
# $ docker build -t gui .
# docker run -i -t -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:rw gui
