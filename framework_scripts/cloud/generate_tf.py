import yaml

with open("input.yaml", "r") as f:
    config = yaml.safe_load(f)

terraform_content = f'''
provider "aws" {{
  region = "{config['region']}"
}}

resource "aws_security_group" "ssh" {{
  name = "allow_ssh"

  ingress {{
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

resource "aws_instance" "test_server" {{
  count         = {config['count']}
  ami           = "{config['ami']}"
  instance_type = "{config['instance_type']}"
  key_name      = "{config['key_name']}"

  vpc_security_group_ids = [aws_security_group.ssh.id]

  user_data = file("user_data.yaml")

  tags = {{
    Name = "HPC-Instance-${{count.index}}"
  }}
}}

output "instance_public_ip" {{
  value = aws_instance.test_server[0].public_ip
}}
'''

with open("main.tf", "w") as f:
    f.write(terraform_content)

print("Terraform file generated successfully")