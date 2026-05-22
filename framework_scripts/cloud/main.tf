
provider "aws" {
  region = "us-east-1"
}

resource "aws_security_group" "ssh" {
  name = "allow_ssh"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "test_server" {
  count         = 1
  ami           = "ami-0236922087fa98b6e"
  instance_type = "t2.micro"
  key_name      = "cloud-session"

  vpc_security_group_ids = [aws_security_group.ssh.id]

  user_data = file("user_data.yaml")

  tags = {
    Name = "HPC-Instance-${count.index}"
  }
}

output "instance_public_ip" {
  value = aws_instance.test_server[0].public_ip
}
