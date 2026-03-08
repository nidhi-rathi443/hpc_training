#!/bin/bash

set -e

echo " HPC TOOLCHAIN CLEANUP STARTED"

INSTALL_DIR=/opt/hpc
SRC_DIR=/tmp/hpc_sources

echo "Removing installed toolchain..."

sudo rm -rf $INSTALL_DIR
sudo rm -rf $SRC_DIR

if [ -f /etc/debian_version ]; then
    PKG="apt"

elif command -v dnf >/dev/null 2>&1; then
    PKG="dnf"

else
    echo "Unsupported distro"
    exit 1
fi

# Remove dependencies

if [ -f /etc/debian_version ]; then

    sudo apt remove -y \
        build-essential \
        wget \
        curl \
        cmake \
        libssl-dev \
        zlib1g-dev \
        libffi-dev \
        libbz2-dev \
        libreadline-dev

    sudo apt autoremove -y

elif [ -f /etc/redhat-release ]; then

    echo "Removing dependencies..."

    sudo dnf remove -y \
        gcc gcc-c++ \
        make \
        cmake \
        wget \
        curl \
        openssl-devel \
        bzip2-devel \
        libffi-devel \
        zlib-devel

    sudo dnf autoremove -y
    sudo dnf clean all

fi

echo "Cleanup complete"
