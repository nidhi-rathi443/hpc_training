import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")


def run_script(script_name, args=None):

    script_path = os.path.join(SCRIPTS_DIR, script_name)

    if not os.path.exists(script_path):
        print(f"[ERROR] Script {script_name} not found.")
        sys.exit(1)

    print(f"\n[INFO] Executing {script_name}...\n")

    cmd = ["sudo", "bash", script_path]

    if args:
        cmd.append(args)

    try:
        subprocess.run(cmd, check=True)
        print(f"\n[SUCCESS] {script_name} completed.\n")
    except subprocess.CalledProcessError:
        print(f"\n[FAILED] {script_name} execution failed.\n")
        sys.exit(1)


def show_menu():

    print("========== HPC Automation Framework ==========")
    print("1. Install Slurm")
    print("2. Cleanup Slurm")
    print("3. Install GCC + OpenMPI")
    print("4. Cleanup GCC + OpenMPI")
    print("5. Exit")
    print("==============================================")


def main():

    while True:

        show_menu()

        choice = input("Enter your choice: ")

        if choice == "1":

            run_script("slurm_install.sh")

        elif choice == "2":

            print("\nCleanup Mode:")
            print("1. Safe Cleanup")
            print("2. Aggressive Cleanup")

            mode = input("Select mode: ")

            if mode == "1":
                run_script("slurm_full_cleanup.sh", "safe")

            elif mode == "2":
                run_script("slurm_full_cleanup.sh", "aggressive")

            else:
                print("[ERROR] Invalid cleanup option.\n")

        elif choice == "3":

            run_script("gcc_openmpi_install.sh")

        elif choice == "4":

            run_script("gcc_openmpi_cleanup.sh")

        elif choice == "5":

            print("\nExiting HPC Automation Framework.\n")
            sys.exit(0)

        else:

            print("\n[ERROR] Invalid choice. Please try again.\n")


if __name__ == "__main__":
    main()
