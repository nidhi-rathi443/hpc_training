#!/bin/bash
set -e

echo "Removing distro Slurm if present..."

if command -v dnf &>/dev/null; then
    dnf remove -y slurm slurm-libs pmix 2>/dev/null || true
elif command -v apt &>/dev/null; then
    apt purge -y slurm-wlm 2>/dev/null || true
fi

echo "Checking for distro Slurm packages..."

if rpm -qa | grep -q "^slurm-"; then
    echo "Distro Slurm detected. Removing it to avoid conflict..."
    dnf remove -y slurm slurm-libs pmix || true
fi

# CONFIG

MUNGE_VER="0.5.16"
HWLOC_VER="2.11.2"
SLURM_VER="24.11.1"

PREFIX="/opt/hpc"
SRC_DIR="$PREFIX/src"
APP_DIR="$PREFIX/apps"

MUNGE_PREFIX="$APP_DIR/munge/$MUNGE_VER"
HWLOC_PREFIX="$APP_DIR/hwloc/$HWLOC_VER"
SLURM_PREFIX="$APP_DIR/slurm/$SLURM_VER"

# ROOT CHECK

if [[ $EUID -ne 0 ]]; then
  echo "Run as root"
  exit 1
fi

# OS DETECTION

detect_os() {
  if command -v apt &>/dev/null; then
    PKG="apt"
  elif command -v dnf &>/dev/null; then
    PKG="dnf"
  elif command -v yum &>/dev/null; then
    PKG="yum"
  else
    echo "Unsupported OS"
    exit 1
  fi
}

install_deps() {
  case $PKG in
    apt)
      apt update
      apt install -y build-essential wget gcc g++ make \
        libssl-dev libpam0g-dev libncurses-dev \
        mariadb-server libmariadb-dev \
        perl pkg-config bzip2
      ;;
    dnf|yum)
      $PKG install -y gcc gcc-c++ make wget \
        openssl-devel pam-devel ncurses-devel \
        mariadb-server mariadb-devel \
        perl pkgconfig bzip2
      ;;
  esac
}

# USERS

create_user_group() {
  groupadd -r munge 2>/dev/null || true
  useradd -r -g munge -s /sbin/nologin munge 2>/dev/null || true

  groupadd -r slurm 2>/dev/null || true
  useradd -r -g slurm -s /sbin/nologin slurm 2>/dev/null || true
}

# MUNGE BUILD

install_munge() {

  echo "Installing Munge from distro..."

  if command -v dnf &>/dev/null; then
      dnf install -y munge munge-libs
  elif command -v apt &>/dev/null; then
      apt install -y munge libmunge-dev
  fi

  systemctl enable munge
  systemctl start munge

  if ! systemctl is-active --quiet munge; then
      echo "Munge failed to start"
      exit 1
  fi
}

# HWLOC BUILD

build_hwloc() {

  if [ -d "$HWLOC_PREFIX" ]; then
    echo "hwloc already installed"
    return
  fi

  cd $SRC_DIR
  wget -nc https://download.open-mpi.org/release/hwloc/v2.11/hwloc-$HWLOC_VER.tar.bz2
  tar -xf hwloc-$HWLOC_VER.tar.bz2
  cd hwloc-$HWLOC_VER

  ./configure --prefix=$HWLOC_PREFIX
  make -j$(nproc)
  make install
}

# SLURM BUILD

build_slurm() {

  if [ -x "$SLURM_PREFIX/sbin/slurmctld" ]; then
    echo "Slurm already installed"
    return
  fi

  cd $SRC_DIR
  wget -nc https://download.schedmd.com/slurm/slurm-$SLURM_VER.tar.bz2
  tar -xf slurm-$SLURM_VER.tar.bz2
  cd slurm-$SLURM_VER

  ./configure \
  --prefix=$SLURM_PREFIX \
  --sysconfdir=/etc/slurm \
  --with-munge=/usr \
  --with-hwloc=$HWLOC_PREFIX

  make -j$(nproc)
  make install
}

echo "Setting system-wide PATH..."

cat > /etc/profile.d/hpc.sh <<EOF
export PATH=$SLURM_PREFIX/bin:$SLURM_PREFIX/sbin:$MUNGE_PREFIX/sbin:\$PATH
EOF

chmod +x /etc/profile.d/hpc.sh

# DATABASE

setup_db() {
  systemctl enable mariadb || true
  systemctl start mariadb || true

  mysql -u root -e "CREATE DATABASE IF NOT EXISTS slurm_acct_db;"
  mysql -u root -e "CREATE USER IF NOT EXISTS 'slurm'@'localhost';"
  mysql -u root -e "GRANT ALL PRIVILEGES ON slurm_acct_db.* TO 'slurm'@'localhost';"
  mysql -u root -e "FLUSH PRIVILEGES;"
}

# SLURM CONFIG

generate_slurm_conf() {

  mkdir -p /etc/slurm

  cat > /etc/slurm/slurm.conf <<EOF
ClusterName=cluster
SlurmctldHost=$(hostname)
SlurmUser=slurm
StateSaveLocation=/var/spool/slurmctld
SlurmdSpoolDir=/var/spool/slurmd
SlurmctldPidFile=/run/slurm/slurmctld.pid
SlurmdPidFile=/run/slurm/slurmd.pid
AuthType=auth/munge
SelectType=select/cons_tres
SchedulerType=sched/backfill
AccountingStorageType=accounting_storage/slurmdbd
EOF

  $SLURM_PREFIX/sbin/slurmd -C | head -n1 >> /etc/slurm/slurm.conf
  echo "PartitionName=debug Nodes=ALL Default=YES MaxTime=INFINITE State=UP" >> /etc/slurm/slurm.conf
}

# DIRECTORIES

setup_dirs() {

  mkdir -p /var/spool/slurmctld /var/spool/slurmd
  mkdir -p /var/log/slurm /run/slurm

  chown -R slurm:slurm /var/spool/slurmctld
  chown -R slurm:slurm /var/spool/slurmd
  chown -R slurm:slurm /var/log/slurm
}

# SYSTEMD SERVICES

create_services() {

cat > /etc/systemd/system/slurmctld.service <<EOF
[Unit]
Description=Slurm controller daemon
After=network.target

[Service]
Type=simple
ExecStart=$SLURM_PREFIX/sbin/slurmctld -D
RuntimeDirectory=slurm
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/slurmd.service <<EOF
[Unit]
Description=Slurm node daemon
After=network.target

[Service]
Type=simple
ExecStart=$SLURM_PREFIX/sbin/slurmd -D
RuntimeDirectory=slurm
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
}

# START SERVICES

if [ ! -S /run/munge/munge.socket.2 ]; then
    echo "Munge socket missing. Aborting."
    exit 1
fi

start_services() {

  systemctl enable slurmctld slurmd || true
  systemctl restart slurmctld || true
  systemctl restart slurmd || true
}

# MAIN

main() {

  detect_os
  install_deps
  create_user_group
  install_munge
  build_hwloc
  build_slurm
  setup_db
  generate_slurm_conf
  setup_dirs
  create_services
  start_services

  echo "Installation complete"
  echo "Test with: sinfo"
}

main
