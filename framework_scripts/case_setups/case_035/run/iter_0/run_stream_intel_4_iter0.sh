#!/bin/bash
#SBATCH --job-name=stream_intel_4_iter0
#SBATCH --partition=Mini-Caribou
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --output=case_setups/case_035/run/iter_0/stream_intel_4_iter0.out

echo "===== JOB START ====="
echo "Running stream | intel | Threads=4"

source modules/intel.sh
echo "Loaded compiler: intel"
which mpirun
echo "CC=$CC"

export OMP_NUM_THREADS=4
export OMP_PROC_BIND=true
export OMP_PLACES=cores

cd $SLURM_SUBMIT_DIR/benchmarks/stream/intel

TOTAL_CORES=${SLURM_CPUS_ON_NODE:-4}
MPI_PROCS=$((TOTAL_CORES / 4))

echo "Total cores: $TOTAL_CORES"
echo "OMP threads: 4"
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
