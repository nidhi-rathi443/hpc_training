import yaml
import json
import subprocess

with open("input.yaml", "r") as f:
    config = yaml.safe_load(f)

with open("output.json", "r") as f:
    output = json.load(f)

pem_file = config["pem_file"]
username = config["username"]

ip = output["instance_ip"]

print(f"Connecting to {ip}")

ssh_command = [
    "ssh",
    "-o",
    "StrictHostKeyChecking=no",
    "-i",
    pem_file,
    f"{username}@{ip}"
]

subprocess.run(ssh_command)