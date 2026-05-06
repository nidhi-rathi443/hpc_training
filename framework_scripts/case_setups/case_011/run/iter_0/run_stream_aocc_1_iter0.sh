#!/bin/bash
#SBATCH --job-name=stream_aocc_1_iter0
#SBATCH --partition=Mini-Caribou
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:30:00
#SBATCH --output=case_setups/case_011/run/iter_0/stream_aocc_1_iter0.out

echo "===== JOB START ====="
echo "Running stream | aocc | Threads=1"

source modules/aocc.sh
echo "Loaded compiler: aocc"
which mpirun
echo "CC=$CC"

export OMP_NUM_THREADS=1
export OMP_PROC_BIND=true
export OMP_PLACES=cores

cd $SLURM_SUBMIT_DIR/benchmarks/stream/aocc

TOTAL_CORES=${SLURM_CPUS_ON_NODE:-4}
MPI_PROCS=$((TOTAL_CORES / 1))

echo "Total cores: $TOTAL_CORES"
echo "OMP threads: 1"
echo "MPI procs: $MPI_PROCS"

case "stream" in
  hpl)
    mpirun -np $MPI_PROCS ./xhpl
    ;;
  hpcg)
    mpirun -np $MPI_PROCS ./xhpcg
    echo "===== HPCG OUTPUT ====="
    file=$(ls -t HPCG-Benchmark_*.txt 2>/dev/null | head -1)
    [ -f "$file" ] && cat "$file"
    ;;
  stream)
    ./stream
    ;;
esac

echo "===== JOB END ====="
