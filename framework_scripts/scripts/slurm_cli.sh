#!/bin/bash

VERSION="1.0.0"
AUTHOR="Nidhi Rathi"
BUILD_DATE=$(date +"%Y-%m-%d")
INSTALL_SCRIPT="./slurm_install.sh"
CLEAN_SCRIPT="./slurm_full_cleanup.sh"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m'

print_banner() {
echo -e "${BLUE}"
echo "        SLURM HPC FRAMEWORK"
echo "Version : $VERSION"
echo "Author  : $AUTHOR"
echo "Build   : $BUILD_DATE"
echo -e "${NC}"
}

print_help() {
print_banner
echo -e "${YELLOW}Usage:${NC}"
echo "  ./slurm_cli.sh [OPTION]"
echo ""

echo -e "${YELLOW}Options:${NC}"
echo "  --install           Install Slurm framework"
echo "  --cleanup           Safe cleanup"
echo "  --cleanup-all       Aggressive cleanup"
echo "  --status            Show cluster status"
echo "  --partition <name>  Change default partition"
echo "  --upgrade           Upgrade / reinstall Slurm"
echo "  --version           Show framework version"
echo "  --doctor            Show cluster-health"
echo "  --logs              Show logs"
echo "  --cluster_info      Show cluster-information"
echo "  --submit_test_job   Show submitting a test job"
echo "  --help              Show this help message"
echo ""
}

show_status() {
print_banner

echo -e "${GREEN}Service Status:${NC}"

echo -n "munge      : "
systemctl is-active munge

echo -n "slurmdbd   : "
systemctl is-active slurmdbd

echo -n "slurmctld  : "
systemctl is-active slurmctld

echo -n "slurmd     : "
systemctl is-active slurmd

echo ""
echo -e "${GREEN}Cluster Info:${NC}"
sinfo 2>/dev/null || echo "Slurm not responding"
}

change_partition() {
    NEW_PARTITION=$1
    if [ -z "$NEW_PARTITION" ]; then
        echo -e "${RED}Partition name required${NC}"
        exit 1
    fi

    sudo sed -i "s/^PartitionName=.*/PartitionName=$NEW_PARTITION Nodes=ALL Default=YES MaxTime=INFINITE State=UP/" /etc/slurm/slurm.conf

    sudo systemctl restart slurmctld
    echo -e "${GREEN}Partition changed to $NEW_PARTITION${NC}"
}

check_cluster_health() {

echo -e "Checking Slurm services..."

systemctl is-active munge
systemctl is-active slurmctld
systemctl is-active slurmd
systemctl is-active slurmdbd

echo ""
echo -e "Cluster nodes:"
sinfo

}

cluster_info() {

echo -e "===== Cluster Information ====="

echo
echo -e "Hostname:"
hostname

echo
echo -e "CPU Info:"
lscpu | grep "Model name"

echo
echo -e "Memory:"
free -h

echo
echo -e "Slurm Partition:"
sinfo

echo
echo -e "Nodes:"
scontrol show nodes
}

logs(){

echo -e "===== Recent Slurm Logs ====="

journalctl -u slurmctld -n 10 --no-pager
journalctl -u slurmd -n 10 --no-pager
}

submit_test_job() {

echo "Submitting test job to Slurm..."

cat <<EOF > /tmp/hpc_test_job.sh
#!/bin/bash
#SBATCH --job-name=hpc_test
#SBATCH --output=/tmp/hpc_test.out
#SBATCH --time=00:01:00

echo "Running on:"
hostname
sleep 30
echo "Test job completed"
EOF

chmod +x /tmp/hpc_test_job.sh

JOBID=$(sbatch /tmp/hpc_test_job.sh | awk '{print $4}')

echo "Job submitted with ID: $JOBID"

echo "Waiting for job to complete..."

sleep 5

echo
echo "Job Output:"
cat /tmp/hpc_test.out
}

case "$1" in

--install)
echo -e "${GREEN}Starting Slurm Installation...${NC}"
sudo bash $INSTALL_SCRIPT
;;

--cleanup)
echo -e "${YELLOW}Running Safe Cleanup...${NC}"
sudo bash $CLEAN_SCRIPT safe
;;

--cleanup-all)
echo -e "${RED}Running Aggressive Cleanup...${NC}"
sudo bash $CLEAN_SCRIPT aggressive
;;

--status)
show_status
;;

--partition)
change_partition $2
;;

--upgrade)
echo -e "${GREEN}Running Upgrade...${NC}"
sudo bash $INSTALL_SCRIPT
;;

--version)
print_banner
echo "Slurm Framework Version: $VERSION"
;;

--help)
print_help
;;

--doctor)
check_cluster_health
;;

--cluster_info)
cluster_info
;;

--logs)
logs
;;

--submit_test_job)
submit_test_job
;;

*)
echo -e "${RED}Invalid option: $1${NC}"
print_help
;;

esac


# ./slurm_cli.sh --status
# ./slurm_cli.sh --submit_test_job
# bash slurm_cli.sh --partition HPC
# bash slurm_cli.sh --version

# python3 cli.py --logs
# python3 cli.py --cluster_info
# python3 cli.py --doctor