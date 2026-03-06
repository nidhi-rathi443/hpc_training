#!/bin/bash

set -e

echo " HPC TOOLCHAIN CLEANUP STARTED"

INSTALL_DIR=/opt/hpc
SRC_DIR=/tmp/hpc_sources

echo "Removing installed toolchain..."

sudo rm -rf $INSTALL_DIR
sudo rm -rf $SRC_DIR

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

    sudo yum groupremove -y "Development Tools"

    sudo yum remove -y \
        wget \
        curl \
        cmake \
        openssl-devel \
        bzip2-devel \
        libffi-devel \
        zlib-devel

fi

echo "Cleanup complete"
