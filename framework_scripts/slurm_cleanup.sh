#!/bin/bash
set -e

echo "Stopping services..."

systemctl stop slurmd 2>/dev/null || true
systemctl stop slurmctld 2>/dev/null || true
systemctl stop slurmdbd 2>/dev/null || true
systemctl stop munge 2>/dev/null || true
systemctl stop mariadb 2>/dev/null || true

echo "Disabling services..."

systemctl disable slurmd 2>/dev/null || true
systemctl disable slurmctld 2>/dev/null || true
systemctl disable slurmdbd 2>/dev/null || true
systemctl disable munge 2>/dev/null || true
systemctl disable mariadb 2>/dev/null || true

echo "Removing systemd service files..."

rm -f /etc/systemd/system/slurmctld.service
rm -f /etc/systemd/system/slurmd.service
rm -f /etc/systemd/system/slurmdbd.service

systemctl daemon-reload

echo "Removing installation directories..."

rm -rf /opt/hpc

echo "Removing configuration files..."

rm -rf /etc/slurm
rm -rf /etc/munge

echo "Removing runtime, spool, and log directories..."

rm -rf /var/spool/slurmctld
rm -rf /var/spool/slurmd
rm -rf /var/log/slurm
rm -rf /var/log/munge
rm -rf /var/lib/munge
rm -rf /run/slurm

echo "Dropping Slurm database (if exists)..."

mysql -u root -e "DROP DATABASE IF EXISTS slurm_acct_db;" 2>/dev/null || true
mysql -u root -e "DROP USER IF EXISTS 'slurm'@'localhost';" 2>/dev/null || true

echo "Removing users and groups..."

userdel -r slurm 2>/dev/null || true
groupdel slurm 2>/dev/null || true

userdel -r munge 2>/dev/null || true
groupdel munge 2>/dev/null || true

echo "Removing PATH entries (if added)..."

sed -i '/opt\/hpc\/apps/d' /root/.bashrc 2>/dev/null || true
sed -i '/opt\/hpc\/apps/d' /home/*/.bashrc 2>/dev/null || true

echo "Cleanup complete."

echo "System is now clean of Slurm, Munge, and HPC stack."

echo "Removing system packages if present..."

if command -v apt &>/dev/null; then
    apt purge -y munge libmunge-dev mariadb-server mariadb-client 2>/dev/null || true
    apt autoremove -y
elif command -v dnf &>/dev/null; then
    dnf remove -y munge munge-libs mariadb-server 2>/dev/null || true
elif command -v yum &>/dev/null; then
    yum remove -y munge munge-libs mariadb-server 2>/dev/null || true
fi
