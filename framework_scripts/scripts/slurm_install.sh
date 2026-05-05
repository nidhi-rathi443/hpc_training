#!/bin/bash
set -e

SLURM_VER="24.11.1"
HWLOC_VER="2.11.2"

BASE_DIR="/opt/hpc"
SRC_DIR="$BASE_DIR/src"

SLURM_PREFIX="$BASE_DIR/apps/slurm/$SLURM_VER"
HWLOC_PREFIX="$BASE_DIR/apps/hwloc/$HWLOC_VER"

SLURM_CONF="/etc/slurm/slurm.conf"
SLURMDBD_CONF="/etc/slurm/slurmdbd.conf"

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        echo "Cannot detect OS"
        exit 1
    fi

    echo "Detected OS: $OS $VERSION"
}

install_dependencies() {

    echo "Installing build dependencies..."

    if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
        apt update
        apt install -y build-essential wget tar \
        munge libmunge-dev libssl-dev libpam0g-dev \
        mariadb-server libmariadb-dev \
        hwloc libhwloc-dev pkg-config
    elif [[ "$OS" == "fedora" ]]; then
        dnf install -y gcc gcc-c++ make wget tar \
        munge munge-devel openssl-devel pam-devel \
        mariadb-server mariadb-devel \
        hwloc hwloc-devel
    else
        echo "Unsupported OS"
        exit 1
    fi
}

create_users() {

    id munge &>/dev/null || useradd -r -s /sbin/nologin munge
    id slurm &>/dev/null || useradd -r -m -d /var/lib/slurm slurm

}

# munge setup(skip if installed)
setup_munge() {

    if systemctl is-active --quiet munge; then
        echo "Munge already running"
        return
    fi

    mkdir -p /etc/munge
    chown munge:munge /etc/munge

    if [ ! -f /etc/munge/munge.key ]; then
        sudo -u munge /usr/sbin/mungekey --create
    fi

    chmod 400 /etc/munge/munge.key
    chown munge:munge /etc/munge/munge.key

    systemctl enable munge
    systemctl restart munge
}

# Mariadb setup(skip if installed)
setup_database() {

    systemctl enable mariadb || systemctl enable mysql
    systemctl start mariadb || systemctl start mysql

    mysql -e "CREATE DATABASE IF NOT EXISTS slurm_acct_db;"
    mysql -e "CREATE USER IF NOT EXISTS 'slurm'@'localhost';"
    mysql -e "GRANT ALL PRIVILEGES ON slurm_acct_db.* TO 'slurm'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"
}

# Build hwloc(skip if installed)
build_hwloc() {

    if command -v lstopo &>/dev/null; then
        echo "hwloc already installed"
        return
    fi

    mkdir -p $SRC_DIR
    cd $SRC_DIR
    wget -nc https://download.open-mpi.org/release/hwloc/v2.11/hwloc-2.11.2.tar.bz2
    tar -xf hwloc-2.11.2.tar.bz2
    cd hwloc-2.11.2

    ./configure --prefix=/opt/hpc/apps/hwloc/2.11.2
    make -j$(nproc)
    make install
}

# Build slurm
build_slurm() {

    if command -v slurmctld &>/dev/null; then
        echo "Slurm already installed"
        return
    fi

    mkdir -p $SRC_DIR
    cd $SRC_DIR
    wget -nc https://download.schedmd.com/slurm/slurm-24.11.1.tar.bz2
    tar -xf slurm-24.11.1.tar.bz2
    cd slurm-24.11.1

    ./configure \
    --prefix=/opt/hpc/apps/slurm/24.11.1 \
    --sysconfdir=/etc/slurm \
    --with-munge \
    --with-hwloc=/opt/hpc/apps/hwloc/2.11.2 \
    --with-mysql

    make -j$(nproc)
    make install

    echo 'export PATH=/opt/hpc/apps/slurm/24.11.1/bin:/opt/hpc/apps/slurm/24.11.1/sbin:$PATH' >> /etc/profile
}

# create directories
create_directories() {

    mkdir -p /var/spool/slurmctld
    mkdir -p /var/spool/slurmd
    mkdir -p /var/log/slurm

    chown -R slurm:slurm /var/spool/slurmctld
    chown -R slurm:slurm /var/spool/slurmd
    chown -R slurm:slurm /var/log/slurm
}

# Config generator
generate_configs() {

mkdir -p /etc/slurm

cat > /etc/slurm/slurm.conf <<EOF
ClusterName=cluster
SlurmctldHost=$(hostname)
SlurmUser=slurm

StateSaveLocation=/var/spool/slurmctld
SlurmdSpoolDir=/var/spool/slurmd

AuthType=auth/munge
SelectType=select/cons_tres
AccountingStorageType=accounting_storage/slurmdbd

NodeName=$(hostname) CPUs=2 RealMemory=2000 State=UNKNOWN
PartitionName=debug Nodes=ALL Default=YES MaxTime=INFINITE State=UP
EOF
}

# slurmdbd config
generate_slurmdbd_conf() {

cat > /etc/slurm/slurmdbd.conf <<EOF
AuthType=auth/munge
DbdHost=localhost
SlurmUser=slurm
StorageType=accounting_storage/mysql
StorageHost=localhost
StorageUser=slurm
StorageLoc=slurm_acct_db
EOF

chmod 600 /etc/slurm/slurmdbd.conf
chown slurm:slurm /etc/slurm/slurmdbd.conf
}

# create services

create_services() {

    # slurmctld
    if [ ! -f /etc/systemd/system/slurmctld.service ]; then
        cat > /etc/systemd/system/slurmctld.service <<EOF
[Unit]
Description=Slurm controller daemon
After=network.target munge.service mariadb.service

[Service]
Type=simple
User=slurm
ExecStart=$SLURM_PREFIX/sbin/slurmctld -D
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
    fi


    # slurmd
    if [ ! -f /etc/systemd/system/slurmd.service ]; then
        cat > /etc/systemd/system/slurmd.service <<EOF
[Unit]
Description=Slurm node daemon
After=network.target munge.service slurmctld.service

[Service]
Type=simple
User=root
ExecStart=$SLURM_PREFIX/sbin/slurmd -D
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
    fi


    # slurmdbd
    if [ ! -f /etc/systemd/system/slurmdbd.service ]; then
        cat > /etc/systemd/system/slurmdbd.service <<EOF
[Unit]
Description=Slurm database daemon
After=network.target munge.service mariadb.service

[Service]
Type=simple
User=slurm
ExecStart=$SLURM_PREFIX/sbin/slurmdbd -D
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
    fi

    systemctl daemon-reload
}

# start services
start_services() {

    echo "Starting services..."

    systemctl enable mariadb || systemctl enable mysql
    systemctl restart mariadb || systemctl restart mysql

    systemctl enable munge
    systemctl restart munge

    systemctl enable slurmdbd
    systemctl start slurmdbd

    sleep 2

    systemctl enable slurmctld
    systemctl start slurmctld

    systemctl enable slurmd
    systemctl start slurmd

    echo "Service status:"
    systemctl status munge --no-pager
    systemctl status slurmdbd --no-pager
    systemctl status slurmctld --no-pager
    systemctl status slurmd --no-pager
}

# validation
validate_install() {

    export PATH=$SLURM_PREFIX/bin:$SLURM_PREFIX/sbin:$PATH

    sleep 3

    if [ ! -x "$SLURM_PREFIX/bin/sinfo" ]; then
        echo "Slurm installation failed"
        exit 1
    fi

    echo "Cluster status:"
    $SLURM_PREFIX/bin/sinfo

    echo "Testing job submission:"
    $SLURM_PREFIX/bin/srun hostname
}


# main 
main() {
    detect_os
    install_dependencies
    create_users
    setup_munge
    setup_database
    build_hwloc
    build_slurm
    create_directories
    generate_configs
    generate_slurmdbd_conf
    create_services
    start_services
    validate_install
}

main