#!/bin/bash
set -e

INSTALL_DIR=/opt/hpc
SRC_DIR=/tmp/hpc_sources

echo " HPC TOOLCHAIN INSTALLATION STARTED"

mkdir -p $INSTALL_DIR
mkdir -p $SRC_DIR

# Detect Package Manager

detect_package_manager() {

if [ -f /etc/debian_version ]; then
    PKG="apt"
elif [ -f /etc/redhat-release ]; then
    PKG="yum"
else
    echo "Unsupported Linux distribution"
    exit 1
fi

}

# Install Dependencies

install_dependencies() {

echo "Installing required dependencies..."

if [ "$PKG" = "apt" ]; then

    sudo apt update

    sudo apt install -y \
        build-essential \
        wget \
        curl \
        tar \
        make \
        cmake \
        libssl-dev \
        zlib1g-dev \
        libffi-dev \
        libbz2-dev \
        libreadline-dev

elif [ "$PKG" = "yum" ]; then

    sudo yum groupinstall -y "Development Tools"

    sudo yum install -y \
        wget \
        curl \
        tar \
        make \
        cmake \
        openssl-devel \
        bzip2-devel \
        libffi-devel \
        zlib-devel

fi

}

# Install GCC

install_gcc() {

if command -v gcc >/dev/null 2>&1; then
    echo "GCC already installed"
    gcc --version | head -1
    return
fi

echo "Installing GCC from source..."

cd $SRC_DIR

wget https://ftp.gnu.org/gnu/gcc/gcc-13.2.0/gcc-13.2.0.tar.gz

tar -xzf gcc-13.2.0.tar.gz

cd gcc-13.2.0

./contrib/download_prerequisites

mkdir build
cd build

../configure \
--prefix=$INSTALL_DIR/gcc \
--enable-languages=c,c++ \
--disable-multilib

make -j$(nproc)

sudo make install

export PATH=$INSTALL_DIR/gcc/bin:$PATH

echo "GCC Installed Successfully"
gcc --version | head -1

}

# Install Python3

install_python() {

if command -v python3 >/dev/null 2>&1; then
    echo "Python3 already installed"
    python3 --version
    return
fi

echo "Installing Python3 from source..."

cd $SRC_DIR

wget https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tgz

tar -xzf Python-3.12.2.tgz

cd Python-3.12.2

./configure \
--prefix=$INSTALL_DIR/python3 \
--enable-optimizations

make -j$(nproc)

sudo make install

export PATH=$INSTALL_DIR/python3/bin:$PATH

python3 --version

}

# Install OpenMPI

install_openmpi() {

if command -v mpirun >/dev/null 2>&1; then
    echo "OpenMPI already installed"
    mpirun --version | head -1
    return
fi

echo "Installing OpenMPI from source..."

cd $SRC_DIR

wget https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-4.1.6.tar.gz

tar -xzf openmpi-4.1.6.tar.gz

cd openmpi-4.1.6

./configure \
--prefix=$INSTALL_DIR/openmpi

make -j$(nproc)

sudo make install

export PATH=$INSTALL_DIR/openmpi/bin:$PATH

mpirun --version | head -1

}

# Verification

verify_installation() {

echo "VERIFYING INSTALLATION"

gcc --version | head -1
python3 --version
mpirun --version | head -1

}

# MAIN

detect_package_manager
install_dependencies
install_gcc
install_python
install_openmpi
verify_installation

echo " HPC TOOLCHAIN INSTALLATION COMPLETE"
