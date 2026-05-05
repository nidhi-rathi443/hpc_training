#!/bin/bash
#SBATCH --job-name=test
#SBATCH --output=output.txt

hostname
sleep 5
echo "Job finished"
