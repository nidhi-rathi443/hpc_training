import subprocess

print("Destroying Infrastructure...")

subprocess.run([
    "terraform",
    "destroy",
    "-auto-approve"
], check=True)