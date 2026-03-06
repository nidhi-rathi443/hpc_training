#!/bin/bash
#SBATCH --job-name=test
#SBATCH --output=test.out

echo "Running on:"
hostname
sleep 3
echo "Done"
