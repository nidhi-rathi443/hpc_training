#!/bin/bash
set -e

BASE_DIR="/opt/hpc"
SLURM_CONF_DIR="/etc/slurm"

MODE="$1"   # safe OR aggressive

if [[ "$MODE" != "safe" && "$MODE" != "aggressive" ]]; then
    echo "Usage: sudo bash slurm_framework_cleanup.sh [safe|aggressive]"
    exit 1
fi

echo "Stopping services..."

systemctl stop slurmd 2>/dev/null || true
systemctl stop slurmctld 2>/dev/null || true
systemctl stop slurmdbd 2>/dev/null || true
systemctl stop munge 2>/dev/null || true
systemctl stop mariadb 2>/dev/null || systemctl stop mysql 2>/dev/null || true

echo "Disabling services..."

systemctl disable slurmd 2>/dev/null || true
systemctl disable slurmctld 2>/dev/null || true
systemctl disable slurmdbd 2>/dev/null || true

echo "Removing systemd service files..."

rm -f /etc/systemd/system/slurmctld.service
rm -f /etc/systemd/system/slurmd.service
rm -f /etc/systemd/system/slurmdbd.service

systemctl daemon-reload

echo "Removing Slurm directories..."

rm -rf $SLURM_CONF_DIR
rm -rf /var/spool/slurmctld
rm -rf /var/spool/slurmd
rm -rf /var/log/slurm

rm -rf $BASE_DIR/apps/slurm
rm -rf $BASE_DIR/apps/hwloc
rm -rf $BASE_DIR/src

if [[ "$MODE" == "aggressive" ]]; then

    echo "Aggressive mode: removing users and database..."

    userdel -r slurm 2>/dev/null || true

    mysql -e "DROP DATABASE IF EXISTS slurm_acct_db;" 2>/dev/null || true
    mysql -e "DROP USER IF EXISTS 'slurm'@'localhost';" 2>/dev/null || true

    rm -rf /etc/munge
fi

echo "Cleanup completed."

# sudo bash slurm_full_cleanup.sh safe --- Safe mode (keeps munge + db intact)

# sudo bash slurm_full_cleanup.sh aggressive --- Aggressive mode (removes everything including DB and users)