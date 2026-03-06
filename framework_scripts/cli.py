import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPT = os.path.abspath(
    os.path.join(BASE_DIR, "..", "framework_scripts/scripts/", "slurm_cli.sh")
)

def main():

    if len(sys.argv) < 2:
        print("Usage: python cli.py [--install | --cleanup | --partition | --upgrade | --status | --doctor | --version | --logs | --cluster_info | --submit_test_job | --help ]")
        sys.exit(1)

    flag = sys.argv[1]

    os.system(f"bash {SCRIPT} {flag}")

if __name__ == "__main__":
    main()