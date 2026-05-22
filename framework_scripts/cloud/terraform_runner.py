import subprocess
import json

print("Initializing Terraform...")
subprocess.run(["terraform", "init"], check=True)

print("Applying Terraform...")
subprocess.run([
    "terraform",
    "apply",
    "-auto-approve"
], check=True)

print("Fetching Outputs...")
result = subprocess.check_output([
    "terraform",
    "output",
    "-json"
])

output = json.loads(result)

ip = output["instance_public_ip"]["value"]

final_output = {
    "instance_ip": ip
}

with open("output.json", "w") as f:
    json.dump(final_output, f, indent=4)

print("Output file generated")
print(final_output)