#!/usr/bin/env python3

import sys
import subprocess
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INSTALL_SCRIPT = os.path.join(BASE_DIR, "scripts", "install_toolchain.sh")
CLEANUP_SCRIPT = os.path.join(BASE_DIR, "scripts", "cleanup_toolchain.sh")


def run_script(script):
    if not os.path.exists(script):
        print(f"Script not found: {script}")
        sys.exit(1)

    try:
        subprocess.run(["bash", script], check=True)
    except subprocess.CalledProcessError:
        print("Error occurred while running script")
        sys.exit(1)


def show_help():
    print("""
Usage:
    python3 toolchain.py --install_toolchain
    python3 toolchain.py --cleanup_toolchain
    python3 toolchain.py --status
""")

def check_status():

    tools = {
        "GCC": "gcc",
        "Python3": "python3",
        "OpenMPI": "mpirun"
    }

    print("\nToolchain Status\n")

    for name, cmd in tools.items():
        result = subprocess.run(
            ["which", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode == 0:
            print(f"{name}: Installed")
        else:
            print(f"{name}: Not Installed")


def main():

    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    arg = sys.argv[1]

    if arg == "--install_toolchain":
        print("Starting HPC toolchain installation...")
        run_script(INSTALL_SCRIPT)

    elif arg == "--cleanup_toolchain":
        print("Starting HPC toolchain cleanup...")
        run_script(CLEANUP_SCRIPT)

    elif arg == "--status":
        check_status()

    else:
        print("Invalid option:", arg)
        show_help()


if __name__ == "__main__":
    main()


# python3 toolchain.py --status
# python3 toolchain.py --install_toolchain
# python3 toolchain.py --cleanup_toolchain
# python3 toolchain.py --test_mpi

