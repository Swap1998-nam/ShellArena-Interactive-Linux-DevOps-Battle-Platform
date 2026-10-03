FROM ubuntu:24.04
RUN useradd --uid 10001 --create-home arena \
    && mkdir /workspace && chown arena:arena /workspace
USER 10001:10001
WORKDIR /workspace
CMD ["/bin/bash"]
