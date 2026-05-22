import subprocess
import sys
import os
from benchmark_copy import run_benchmarks

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

def show_help():
    print("""
Usage:
  python3 main.py benchmark --app <hpl|hpcg|stream> --compiler <aocc|intel>

Optional:
  --threads <1 2 4>      Specify threads
  --iterations <n>       Number of runs (default: 2)

Examples:
  python3 main.py benchmark --app hpl --compiler aocc
  python3 main.py benchmark --app stream --compiler intel --threads 1 --iterations 3
""")

def run_script(script_name):
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    if not os.path.exists(script_path):
        print(f"[ERROR] Script {script_name} not found.")
        sys.exit(1)

    print(f"\n[INFO] Executing {script_name}...\n")

    try:
        subprocess.run(["sudo", "bash", script_path], check=True)
        print(f"\n[SUCCESS] {script_name} completed.\n")
    # try:

    #     # ===== SLURM CHECK =====
    #     if script_name == "slurm_install.sh":

    #         check = subprocess.run(
    #             ["which", "slurmctld"],
    #             capture_output=True,
    #             text=True
    #         )

    #         if check.returncode == 0:
    #             print("\n[SUCCESS] Slurm already installed. Skipping installation.\n")
    #             return

    #     # ===== TOOLCHAIN CHECK =====
    #     if script_name == "install_toolchain.sh":

    #         gcc_check = subprocess.run(
    #             ["which", "gcc"],
    #             capture_output=True,
    #             text=True
    #         )

    #         mpirun_check = subprocess.run(
    #             ["which", "mpirun"],
    #             capture_output=True,
    #             text=True
    #         )

    #         if gcc_check.returncode == 0 and mpirun_check.returncode == 0:
    #             print("\n[SUCCESS] Toolchain already installed. Skipping installation.\n")
    #             return

    #     subprocess.run(["sudo", "bash", script_path], check=True)

    #     print(f"\n[SUCCESS] {script_name} completed.\n")
    except subprocess.CalledProcessError:
        print(f"\n[FAILED] {script_name} execution failed.\n")
        sys.exit(1)


# def show_menu():
#     print("========== HPC Automation Framework ==========")
#     print("1. Install Slurm")
#     print("2. Cleanup Slurm")
#     print("3. Install GCC + Python + OpenMPI")
#     print("4. Cleanup GCC + Python + OpenMPI")
#     print("5. Run Benchmarking")
#     print("6. Exit")
#     print("==============================================")

def show_menu():
    print("\033[1;33m" + """
    ██╗  ██╗██████╗  ██████╗
    ██║  ██║██╔══██╗██╔════╝
    ███████║██████╔╝██║     
    ██╔══██║██╔═══╝ ██║     
    ██║  ██║██║     ╚██████╗
    ╚═╝  ╚═╝╚═╝      ╚═════╝
    """ + "\033[0m")

    RESET = "\033[0m"
    BOLD = "\033[1m"

    CYAN = "\033[1;36m"
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[1;31m"
    BLUE = "\033[1;34m"
    MAGENTA = "\033[1;35m"

    print(CYAN + BOLD + "========== HPC Automation Framework ==========" + RESET)

    print(GREEN  + "1. Install Slurm" + RESET)
    print(RED    + "2. Cleanup Slurm" + RESET)
    print(GREEN  + "3. Install GCC + Python + OpenMPI" + RESET)
    print(RED    + "4. Cleanup GCC + Python + OpenMPI" + RESET)
    print(YELLOW + "5. Run Benchmarking" + RESET)
    print(MAGENTA+ "6. Exit" + RESET)

    print(CYAN + BOLD + "==============================================" + RESET)

import difflib

def suggest_flag(wrong_flag, valid_flags):
    matches = difflib.get_close_matches(wrong_flag, valid_flags, n=1, cutoff=0.5)
    return matches[0] if matches else None

def main():

    valid_flags = ["--app", "--compiler", "--threads", "--iterations", "--help"]

    for arg in sys.argv:
        if arg.startswith("--") and arg not in valid_flags:
            suggestion = suggest_flag(arg, valid_flags)

            if suggestion:
                print(f"\nInvalid flag: {arg}")
                print(f"Did you mean '{suggestion}' ?\n")
            else:
                print(f"\nInvalid flag: {arg}\n")

            show_help()
            return

    app = None
    command = None
    threads = None
    iterations = None

    if "--help" in sys.argv or "-h" in sys.argv:
        show_help()
        return

    # parse CLI args
    if len(sys.argv) > 1:
        command = sys.argv[1]

    if "--app" in sys.argv:
        idx = sys.argv.index("--app")
        if idx + 1 < len(sys.argv):
            app = sys.argv[idx + 1]

    if "--compiler" in sys.argv:
        idx = sys.argv.index("--compiler")
        if idx + 1 < len(sys.argv):
            compiler = sys.argv[idx + 1]
    
    if "--threads" in sys.argv:
        try:
            idx = sys.argv.index("--threads")
            threads = int(sys.argv[idx + 1])
        except:
            print("Invalid usage of --threads")
            sys.exit(1)

    if "--iterations" in sys.argv:
        try:
            idx = sys.argv.index("--iterations")
            iterations = int(sys.argv[idx + 1])
        except:
            print("Invalid usage of --iterations")
            sys.exit(1)

    #print("DEBUG iterations from CLI:", iterations)

    if command == "benchmark":
            print("Running Benchmarking...")
            run_benchmarks(app, compiler, threads, iterations)
            return

    valid_flags = ["--app", "--compiler", "--threads", "--iterations", "--help"]

    for arg in sys.argv:
        if arg.startswith("--") and arg not in valid_flags:
            print("\nInvalid flag:", arg)
            show_help()
            return

    if "benchmark" in sys.argv:
        if "--app" not in sys.argv or "--compiler" not in sys.argv:
            print("\nMissing required arguments!")
            show_help()
            return

    """if len(sys.argv) < 2 or sys.argv[1] != "benchmark":
        show_help()
        return"""
    
    while True:
        show_menu()
        choice = input("Enter your choice: ")

        if choice == "1":
            run_script("slurm_install.sh")

        elif choice == "2":
            run_script("slurm_full_cleanup.sh")

        elif choice == "3":
            run_script("install_toolchain.sh")

        elif choice == "4":
            run_script("cleanup_toolchain.sh")

        elif choice == "5":
            print("Running Benchmarking...")
            run_benchmarks()

        elif choice == "6":
            print("Exiting...")
            sys.exit(0)

        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
