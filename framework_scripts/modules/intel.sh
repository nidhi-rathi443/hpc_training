#!/bin/bash
module purge
module load intel-compilers
module load mkl
module load openmpi-intel

export CC=icc
export FC=ifort