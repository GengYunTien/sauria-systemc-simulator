# Stage 1: Build Verilator v4.228
FROM ubuntu:22.04 AS build-verilator
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    git make autoconf g++ flex bison libfl2 libfl-dev zlib1g-dev python3 \
 && rm -rf /var/lib/apt/lists/*
ARG VERILATOR_VERSION=v4.228
RUN git clone https://github.com/verilator/verilator.git /tmp/verilator \
 && cd /tmp/verilator \
 && git checkout ${VERILATOR_VERSION} \
 && autoconf \
 && ./configure --prefix=/opt/verilator \
 && make -j$(nproc) \
 && make install

# Stage 2: Build SystemC 2.3.4
FROM ubuntu:22.04 AS build-systemc
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y git cmake g++ make \
 && rm -rf /var/lib/apt/lists/*
RUN git clone --branch 2.3.4_pub_rev_20190614 --depth 1 \
    https://github.com/accellera-official/systemc.git /tmp/systemc-src \
 && mkdir -p /tmp/systemc-src/docs/tlm \
 && touch /tmp/systemc-src/docs/tlm/ChangeLog \
 && cmake -S /tmp/systemc-src -B /tmp/systemc-src/build \
         -DCMAKE_INSTALL_PREFIX=/opt/systemc \
         -DCMAKE_BUILD_TYPE=Release \
         -DCMAKE_CXX_STANDARD=17 \
 && cmake --build /tmp/systemc-src/build -j$(nproc) \
 && cmake --install /tmp/systemc-src/build

# Stage 3: Final dev image
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    git make cmake g++ flex bison \
    clang \
    perl \
    python3 python3-pip \
    gtkwave \
    libfl2 zlib1g wget curl vim \
 && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/local/bin/python

COPY --from=build-verilator /opt/verilator /opt/verilator
COPY --from=build-systemc   /opt/systemc   /opt/systemc

RUN ln -s /opt/verilator/share/verilator/include /opt/verilator/include

ENV PATH="/opt/verilator/bin:$PATH"
ENV VERILATOR_ROOT=/opt/verilator
ENV SYSTEMC_HOME=/opt/systemc
ENV LD_LIBRARY_PATH="/opt/systemc/lib:$LD_LIBRARY_PATH"
ENV CPLUS_INCLUDE_PATH="/opt/systemc/include"

# Python dependencies for SAURIA simulation framework
# PyTorch CPU-only: functionally identical to CUDA build on a CPU-only machine
RUN pip3 install --no-cache-dir \
    torch==2.1.2+cpu \
    torchvision==0.16.2+cpu \
    torchaudio==2.1.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Remaining packages from 3rdparty/sauria/Python/requirements_pip.txt
RUN pip3 install --no-cache-dir \
    numpy==1.23.1 \
    scipy==1.10.0 \
    matplotlib==3.6.2 \
    Pillow==10.0.1 \
    PyYAML==6.0.1 \
    sympy==1.12 \
    networkx==3.1 \
    packaging==23.2 \
    six==1.16.0 \
    python-dateutil==2.8.2 \
    pyparsing==3.1.1 \
    kiwisolver==1.4.5 \
    cycler==0.12.1 \
    fonttools==4.47.0 \
    contourpy==1.1.0 \
    ipykernel \
    python-dotenv

WORKDIR /workspace
CMD ["/bin/bash"]