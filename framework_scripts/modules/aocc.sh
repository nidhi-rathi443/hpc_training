#!/bin/bash
module purge
module load aocc
module load aocl
module load openmpi-aocc

export CC=clang
export FC=flang