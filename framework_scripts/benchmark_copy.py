import os
import subprocess
import yaml
import time
import re
from postprocess import print_build_status, generate_postprocess_report

from rich.console import Console
from rich.table import Table
from rich import box
console = Console()

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def visible_len(text):
    return len(ANSI_ESCAPE.sub('', text))

def pad(text, width):
    return text + " " * (width - visible_len(text))

results = []
from colorama import Fore, Style, init
init(autoreset=True)

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

# def print_box(message, color="default"):
#     WIDTH = 60

#     colors = {
#         "green": "\033[92m",
#         "red": "\033[91m",
#         "cyan": "\033[96m",
#         "yellow": "\033[93m",
#         "default": "\033[0m"
#     }

#     RESET = "\033[0m"
#     c = colors.get(color, colors["default"])

#     print("\n" + c + "+" + "-"*(WIDTH-2) + "+")
#     print("|" + message.center(WIDTH-2) + "|")
#     print("+" + "-"*(WIDTH-2) + "+" + RESET)

def print_box(message, color="default"):
    WIDTH = 60

    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "yellow": "\033[93m",
        "default": "\033[0m"
    }

    RESET = "\033[0m"
    c = colors.get(color, colors["default"])

    print("\n" + c + "+" + "-"*(WIDTH-2) + "+" + RESET)
    print(c + "|" + message.center(WIDTH-2) + "|" + RESET)
    print(c + "+" + "-"*(WIDTH-2) + "+" + RESET)

# ================= CPU CHECK =================
# def get_available_cpus():
#     try:
#         out = subprocess.check_output("sinfo -o '%C'", shell=True).decode()
#         parts = out.strip().split('\n')[1].split('/')
#         idle = int(parts[1])s
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


#================ Next case ID ====================
def get_next_case_id(base_dir="case_setups"):
    os.makedirs(base_dir, exist_ok=True)

    existing = [d for d in os.listdir(base_dir) if d.startswith("case_")]

    if not existing:
        return "case_001"

    nums = []
    for d in existing:
        try:
            num = int(d.split("_")[1])
            nums.append(num)
        except:
            pass

    next_id = max(nums) + 1
    return f"case_{next_id:03d}"


# ================ Create case setup ================
def create_case_setup(bench, compiler, threads):
    case_id = get_next_case_id()
    case_dir = f"case_setups/{case_id}"

    os.makedirs(case_dir, exist_ok=True)
    os.makedirs(f"{case_dir}/run", exist_ok=True)

    # ---- Pretty box ----
    # WIDTH = 60
    # print("\n" + "+" + "-"*(WIDTH-2) + "+")
    # #print("|" + f" CASE SETUP CREATED: {case_id} ".center(WIDTH-2) + "|")
    # print("+" + "-"*(WIDTH-2) + "+")

    # ---- Metadata ----
    with open(f"{case_dir}/metadata.txt", "w") as f:
        f.write(f"Case ID   : {case_id}\n")
        f.write(f"Benchmark : {bench}\n")
        f.write(f"Compiler  : {compiler}\n")
        f.write(f"Threads   : {threads}\n")

    return case_dir


# ================= BUILD SCRIPT =================
def generate_build_script(bench, compiler, case_dir):
    #script_dir = f"benchmarks/{bench}/{compiler}"
    script_dir = f"{case_dir}/build"
    os.makedirs(script_dir, exist_ok=True)

    script_path = f"{script_dir}/build_{bench}_{compiler}.sh"
    #script_path = f"{case_dir}/build/build_{bench}_{compiler}.sh"

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
def generate_run_script(bench, compiler, threads, iteration, run_dir):
    config = load_config()
    SLURM = config["slurm"]
    base_dir = f"benchmarks/{bench}/{compiler}"
    script_dir = base_dir
    log_dir = f"{base_dir}/logs"

    os.makedirs(script_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    job_name = f"{bench}_{compiler}_{threads}_iter{iteration}"
    #script_path = f"{script_dir}/run_{bench}_{compiler}_{threads}_iter{iteration}.sh"
    script_path = f"{run_dir}/run_{job_name}.sh"
    #log_file = f"{log_dir}/{bench}_{compiler}_{threads}_iter{iteration}.out"
    log_file = f"{run_dir}/{job_name}.out"

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

    if result.returncode != 0:
        print(RED + "Job submission failed!" + RESET)
        print("STDERR:", result.stderr.strip())
        return None

    output = result.stdout.strip()
    print("STDOUT:", output)

    # Extract job ID
    try:
        job_id = output.split()[-1]
        return job_id
    except:
        return None

# ================= EXTRACT PERFORMANCE =================
def extract_performance(log_file, bench):
    if not os.path.exists(log_file):
        return "N/A"

    try:
        with open(log_file, "r") as f:
            content = f.readlines()

        # HPL
        if bench == "hpl":
            for line in content:
                if line.strip().startswith("WR"):   # actual result line
                    parts = line.split()
                    try:
                        return parts[-1] + " GFLOPS"
                    except:
                        continue

        # HPCG
        elif bench == "hpcg":
            for line in content:
                if "GFLOP/s rating" in line:
                    return line.split("=")[-1].strip() + " GFLOPS"

        # STREAM
        elif bench == "stream":
            for line in content:
                if "Triad" in line:
                    parts = line.split()
                    if len(parts) > 1:
                        return parts[1] + " MB/s"

    except Exception as e:
        return "ERROR"

    return "N/A"

# ================= MAIN FUNCTION =================
def run_benchmarks(app=None, compiler=None, threads=None, iterations=None):
    config = load_config()
    #iterations = config.get("iterations", 2)
    config_iters = config.get("iterations", 2)

    if iterations is not None:
        final_iters = iterations
    else:
        final_iters = config_iters
    #print("DEBUG iterations inside function:", iterations)

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
    valid_threads = [t for t in THREADS if t <= available and t > 0]

    print(f"Available CPUs: {available}")
    print(f"Running threads: {valid_threads}")

    if compiler:   
        if compiler not in COMPILERS:
            print(f"Invalid compiler: {compiler}")
            print(f"Available compilers: {', '.join(COMPILERS)}")
            return
        selected_compilers = [compiler]
    else:
        selected_compilers = COMPILERS

    if threads:
        if threads not in THREADS:
            print(f"Invalid thread value: {threads}")
            print(f"Available threads: {THREADS}")
            return
        valid_threads = [threads]
    else:
        available = get_available_cpus()
        valid_threads = [t for t in THREADS if t <= available]

    # for comp in selected_compilers:
    #     for bench in selected_benchmarks:

    #         # ===== BUILD STEP =====
    #         build_script = generate_build_script(bench, comp, case_dir)

    #         if not check_binaries(bench, comp):
    #             print(f"{bench} missing → building...")
    #             build_result = subprocess.run(["bash", build_script])
    #             build_status = "SUCCESS" if build_result.returncode == 0 else "FAILED"
    #         else:
    #             print(f"{bench} already exists for {comp} → skipping build")
    #             build_status = "SUCCESS"

    #         # ===== RUN STEP =====
    #         for threads in valid_threads:
    #             case_dir = create_case_setup(bench, comp, threads, i)
    #             for i in range(final_iters):
    #                 iter_dir = f"{case_dir}/run/iter_{i}"
    #                 os.makedirs(iter_dir, exist_ok=True)
    #                 print(f"\nRunning iteration {i+1}/{final_iters} for {bench} | {comp} | threads={threads}")
    #                 run_script = generate_run_script(bench, comp, threads, i, iter_dir)
    #                 print(GREEN + f"Submitting {run_script}" + RESET)
    #                 job_id = submit_job(run_script)
    
    #                 results.append({
    #                     "bench": bench,
    #                     "compiler": comp,
    #                     "threads": threads,
    #                     "job_id": job_id,
    #                     "build_status": build_status,
    #                     #"log": f"benchmarks/{bench}/{comp}/logs/{bench}_{comp}_{threads}_iter{i}.out"
    #                     "log": f"{iter_dir}/{bench}_{comp}_{threads}_iter{i}.out"
    #                 })

    for comp in selected_compilers:
        for bench in selected_benchmarks:
            for threads in valid_threads:

                #  STEP 1: create case ONCE
                case_dir = create_case_setup(bench, comp, threads)
                case_name = case_dir.split("/")[-1]
                print_box(f"CASE SETUP CREATED: {case_name}", "cyan")

                #  STEP 2: build (uses case_dir)
                build_script = generate_build_script(bench, comp, case_dir)

                if not check_binaries(bench, comp):
                    print(f"{bench} missing → building...")
                    build_result = subprocess.run(["bash", build_script])
                    build_status = "SUCCESS" if build_result.returncode == 0 else "FAILED"
                else:
                    print(f"{bench} already exists for {comp} → skipping build")
                    build_status = "SUCCESS"

                #  STEP 3: BUILD BOX 
                if build_status == "SUCCESS":
                    print_box(f"BUILD SUCCESSFUL: {case_name}", "green")
                else:
                    print_box(f"BUILD FAILED: {case_name}", "red")

                #  STEP 4: iterations
                for i in range(final_iters):

                    iter_dir = f"{case_dir}/run/iter_{i}"
                    os.makedirs(iter_dir, exist_ok=True)

                    print(f"\nRunning iteration {i+1}/{final_iters} for {bench} | {comp} | threads={threads}")

                    run_script = generate_run_script(bench, comp, threads, i, iter_dir)

                    print(GREEN + f"Submitting {run_script}" + RESET)
                    job_id = submit_job(run_script)

                    results.append({
                        "bench": bench,
                        "compiler": comp,
                        "threads": threads,
                        "job_id": job_id,
                        "build_status": build_status,
                        "log": f"{iter_dir}/{bench}_{comp}_{threads}_iter{i}.out"
                    })
    
    wait_for_jobs()
    print_summary()
    print_build_status(results)
    generate_postprocess_report(results, extract_performance)

def wait_for_jobs():
    print("\nWaiting for jobs to complete...\n")

    job_ids = [r["job_id"] for r in results if r.get("job_id")]

    while job_ids:
        try:
            out = subprocess.check_output(["squeue", "-h", "-o", "%A"]).decode().split()
            running_jobs = set(out)

            job_ids = [jid for jid in job_ids if jid in running_jobs]

            print(f"Jobs remaining: {len(job_ids)}", end="\r")

            if job_ids:
                time.sleep(5)

        except Exception as e:
            print("Error checking job status:", e)
            break

    print("\nAll jobs completed.\n")

#=============================================================================
#----------------- TRIAL BEGINS-----------------------------------------------
#=============================================================================

# ---- Color helpers ----
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def _get_status(log_path):
    if os.path.exists(log_path):
        if os.path.getsize(log_path) > 0:
            return "COMPLETED"
        else:
            return "FAILED"
    return "NOT FOUND"


def _color_status(status):
    if status == "COMPLETED":
        return f"{GREEN}{status}{RESET}"
    elif status == "FAILED":
        return f"{RED}{status}{RESET}"
    else:
        return f"{YELLOW}{status}{RESET}"
    
COLS = {
    "bench": 10,
    "compiler": 10,
    "threads": 8,
    "status": 12,
    "perf": 18
}

def print_summary():
    if not results:
        console.print("[bold red]No jobs were submitted.[/bold red]")
        return

    total = len(results)
    completed = 0
    failed = 0
    not_found = 0

    for r in results:
        status = _get_status(r["log"])
        if status == "COMPLETED":
            completed += 1
        elif status == "FAILED":
            failed += 1
        else:
            not_found += 1

    # ===== HEADER =====
    #console.print("\n[bold green]MONITORING JOB STATUS[/bold green]")
    print_box("MONITORING JOB STATUS", "green")
    console.print(
        f"Total Jobs Submitted: {total}, "
        f"[green]Jobs Completed: {completed}[/green], "
        f"[yellow]Jobs Missing: {not_found}[/yellow], "
        f"[red]Jobs Failed: {failed}[/red]\n"
    )

    # ===== MAIN TABLE =====
    table = Table(title="Benchmark Results", box=box.DOUBLE_EDGE, expand=True)

    table.add_column("BENCH", justify="left", style="cyan", no_wrap=True)
    table.add_column("COMPILER", style="magenta")
    table.add_column("THREADS", justify="center", style="white")
    table.add_column("STATUS", justify="center")
    table.add_column("PERFORMANCE", justify="right", style="green")

    for r in results:
        status_raw = _get_status(r["log"])
        perf = extract_performance(r["log"], r["bench"])

        if status_raw == "COMPLETED":
            status = "[green]COMPLETED[/green]"
        elif status_raw == "FAILED":
            status = "[red]FAILED[/red]"
        else:
            status = "[yellow]NOT FOUND[/yellow]"

        table.add_row(
            r["bench"],
            r["compiler"],
            str(r["threads"]),
            status,
            perf
        )

    console.print(table)

    # ===== SUCCESS TABLE =====
    success_table = Table(title="Successful Runs", box=box.ROUNDED, expand=True)

    success_table.add_column("SR.N", justify="center")
    success_table.add_column("BENCH")
    success_table.add_column("COMPILER")
    success_table.add_column("THREADS", justify="center")
    success_table.add_column("PERF", justify="right", style="green")

    idx = 1
    for r in results:
        if _get_status(r["log"]) == "COMPLETED":
            perf = extract_performance(r["log"], r["bench"])
            success_table.add_row(
                str(idx),
                r["bench"],
                r["compiler"],
                str(r["threads"]),
                perf
            )
            idx += 1

    if idx == 1:
        success_table.add_row("-", "-", "-", "-", "No successful runs")

    console.print(success_table)

    # ===== FINAL SUMMARY =====
    console.print("\n[bold]FINAL SUMMARY[/bold]")
    console.print(f"[green]TOTAL SUCCESSFUL RUN CASE SETUPS : {completed}[/green]")
    console.print(f"[red]TOTAL RUN FAILED CASE SETUPS     : {failed + not_found}[/red]")


# python3 main.py benchmark --app stream
# scancel --me
# python3 main.py benchmark --app hpl --compiler aocc --threads 2 --iterations 1