import os
import subprocess
import yaml

results = []
from colorama import Fore, Style, init
init(autoreset=True)

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

# ================= CONFIG =================
#COMPILERS = ["aocc", "intel"]
#THREADS = [1, 2, 4]
#BENCHMARKS = ["hpl", "hpcg", "stream"]

#SLURM = {
#    "partition": "HPC",
#    "time": "00:30:00",
#    "nodes": 1
#}

# ================= CPU CHECK =================
# def get_available_cpus():
#     try:
#         out = subprocess.check_output("sinfo -o '%C'", shell=True).decode()
#         parts = out.strip().split('\n')[1].split('/')
#         idle = int(parts[1])
#         return idle
#     except:
#         return 1
def get_available_cpus():
    try:
        return len(os.sched_getaffinity(0))
    except:
        return os.cpu_count() or 1


# ================= RUN SCRIPT TEMPLATE =================
TEMPLATE = """#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --partition={partition}
#SBATCH --nodes={nodes}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={threads}
#SBATCH --time={time}
#SBATCH --output={log_file}

echo "===== JOB START ====="
echo "Running {bench} | {compiler} | Threads={threads}"

source modules/{compiler}.sh
echo "Loaded compiler: {compiler}"
which mpirun
echo "CC=$CC"

export OMP_NUM_THREADS={threads}
export OMP_PROC_BIND=true
export OMP_PLACES=cores

cd $SLURM_SUBMIT_DIR/benchmarks/{bench}/{compiler}

TOTAL_CORES=${{SLURM_CPUS_ON_NODE:-4}}
MPI_PROCS=$((TOTAL_CORES / {threads}))

echo "Total cores: $TOTAL_CORES"
echo "OMP threads: {threads}"
echo "MPI procs: $MPI_PROCS"

case "{bench}" in
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
"""


# ================= BUILD SCRIPT =================
def generate_build_script(bench, compiler):
    script_dir = f"benchmarks/{bench}/{compiler}"
    os.makedirs(script_dir, exist_ok=True)

    script_path = f"{script_dir}/build_{bench}_{compiler}.sh"

    script = f"""#!/bin/bash

echo "Building {bench} with {compiler}"

source modules/{compiler}.sh

case "{bench}" in
  hpl)
    cd $HOME/hpl-2.3 && make
    cp bin/*/xhpl $SLURM_SUBMIT_DIR/benchmarks/hpl/{compiler}/
    ;;
  hpcg)
    cd $HOME/hpcg-HPCG-release-3-1-0 && make
    cp bin/*/xhpcg $SLURM_SUBMIT_DIR/benchmarks/hpcg/{compiler}/
    ;;
  stream)
    cd $HOME/STREAM && make
    cp stream $SLURM_SUBMIT_DIR/benchmarks/stream/{compiler}/
    ;;
esac

echo "Build completed for {bench} ({compiler})"
"""

    with open(script_path, "w") as f:
        f.write(script)

    os.chmod(script_path, 0o755)
    return script_path


# ================= RUN SCRIPT =================
def generate_run_script(bench, compiler, threads):
    config = load_config()
    SLURM = config["slurm"]
    base_dir = f"benchmarks/{bench}/{compiler}"
    script_dir = base_dir
    log_dir = f"{base_dir}/logs"

    os.makedirs(script_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    job_name = f"{bench}_{compiler}_{threads}"
    script_path = f"{script_dir}/run_{job_name}.sh"
    log_file = f"{log_dir}/{job_name}.out"

    content = TEMPLATE.format(
        job_name=job_name,
        partition=SLURM["partition"],
        nodes=SLURM["nodes"],
        threads=threads,
        time=SLURM["time"],
        log_file=log_file,
        bench=bench,
        compiler=compiler
    )

    with open(script_path, "w") as f:
        f.write(content)

    os.chmod(script_path, 0o755)
    return script_path


# ================= CHECK BINARIES =================
def check_binaries(bench, compiler):
    base = f"benchmarks/{bench}/{compiler}"

    if bench == "hpl":
        return os.path.exists(f"{base}/xhpl") and os.path.exists(f"{base}/HPL.dat")

    elif bench == "hpcg":
        return os.path.exists(f"{base}/xhpcg") and os.path.exists(f"{base}/hpcg.dat")

    elif bench == "stream":
        return os.path.exists(f"{base}/stream")

    return False


# ================= SUBMIT =================
def submit_job(job_file):
    result = subprocess.run(["sbatch", job_file], capture_output=True, text=True)
    print("STDOUT:", result.stdout.strip())
    print("STDERR:", result.stderr.strip())

# ================= EXTRACT PERFORMANCE =================
def extract_performance(log_file, bench):
    if not os.path.exists(log_file):
        return "N/A"

    try:
        with open(log_file, "r") as f:
            content = f.read()

        # HPL
        if bench == "hpl":
            for line in content.splitlines():
                if "Gflops" in line or "GFLOPS" in line:
                    parts = line.split()
                    return parts[-1] + " GFLOPS"

        # HPCG
        elif bench == "hpcg":
            for line in content.splitlines():
                if "GFLOP/s rating" in line:
                    return line.split("=")[-1].strip() + " GFLOPS"

        # STREAM
        elif bench == "stream":
            for line in content.splitlines():
                if "Triad" in line:
                    parts = line.split()
                    return parts[1] + " MB/s"

    except:
        return "ERROR"

    return "N/A"

# ================= MAIN FUNCTION =================
def run_benchmarks(app=None, compiler=None):
    config = load_config()

    COMPILERS = config["compilers"]
    THREADS = config["threads"]
    BENCHMARKS = config["benchmarks"]

    if app:
        if app not in BENCHMARKS:
            print(f"Invalid benchmark: {app}")
            print(f"Available benchmarks: {', '.join(BENCHMARKS)}")
            return
        selected_benchmarks = [app]
    else:
        selected_benchmarks = BENCHMARKS

    available = get_available_cpus()
    valid_threads = [t for t in THREADS if t <= available]

    print(f"Available CPUs: {available}")
    print(f"Running threads: {valid_threads}")

    if compiler:   
        if compiler not in COMPILERS:
            print(f"❌ Invalid compiler: {compiler}")
            print(f"Available compilers: {', '.join(COMPILERS)}")
            return
        selected_compilers = [compiler]
    else:
        selected_compilers = COMPILERS

    for comp in selected_compilers:
        for bench in selected_benchmarks:

            # ===== BUILD STEP =====
            build_script = generate_build_script(bench, compiler)

            if not check_binaries(bench, compiler):
                print(f"{bench} missing → building...")
                subprocess.run(["bash", build_script])
            else:
                print(f"{bench} already exists for {compiler} → skipping build")

            # ===== RUN STEP =====
            for threads in valid_threads:
                run_script = generate_run_script(bench, compiler, threads)
                print(Fore.GREEN + f"Submitting {run_script}")
                submit_job(run_script)
        
                results.append({
                    "bench": bench,
                    "compiler": comp,
                    "threads": threads,
                    "log": f"benchmarks/{bench}/{comp}/logs/{bench}_{comp}_{threads}.out"
                })
    
    print_summary()


#--------------working code before making dabba-----------------------------
def print_summary():
    print("\n===== FINAL SUMMARY =====\n")

    print(f"{'Bench':<10}{'Compiler':<10}{'Threads':<10}{'Status':<12}{'Performance'}")
    print("-" * 65)

    for r in results:
        status = "UNKNOWN"

        if os.path.exists(r["log"]):
            if os.path.getsize(r["log"]) > 0:
                status = "COMPLETED"
            else:
                status = "FAILED"
        else:
            status = "NOT FOUND"

        perf = extract_performance(r["log"], r["bench"])

        print(f"{r['bench']:<10}{r['compiler']:<10}{r['threads']:<10}{status:<12}{perf}")

# python3 main.py benchmark --app stream
# scancel --me
