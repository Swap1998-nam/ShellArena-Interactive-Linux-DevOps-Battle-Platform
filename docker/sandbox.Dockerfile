FROM ubuntu:22.04

RUN apt update

RUN apt install -y \
curl \
nano \
vim \
net-tools \
htop

CMD ["/bin/bash"]