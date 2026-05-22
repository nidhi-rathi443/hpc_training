import argparse
import subprocess

parser = argparse.ArgumentParser()

parser.add_argument(
    "--deploy",
    action="store_true",
    help="Deploy cloud infrastructure"
)

parser.add_argument(
    "--benchmark",
    action="store_true",
    help="Run benchmarks on instances"
)

parser.add_argument(
    "--destroy",
    action="store_true",
    help="Destroy infrastructure"
)

args = parser.parse_args()

if args.deploy:
    print("Generating Terraform Files...")
    subprocess.run([
        "python3",
        "generate_tf.py"
    ], check=True)

    print("Running Terraform...")
    subprocess.run([
        "python3",
        "terraform_runner.py"
    ], check=True)

if args.benchmark:
    print("Running Benchmarks...")
    subprocess.run([
        "python3",
        "run_benchmarks.py"
    ], check=True)

if args.destroy:
    subprocess.run([
        "python3",
        "destroy.py"
    ], check=True)