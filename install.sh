#!/bin/bash
#
# Installation framework for lightshowPi
#
# Support for each individual distribution is in install-scripts/
INSTALL_DIR="$( cd $(dirname $0) ; pwd -P )"
BUILD_DIR=${INSTALL_DIR}/build_dir

# Globals populated below
BASE_DISTRO=
DISTRO=

# Globals populated by distro-specific scripts
INSTALL_COMMAND=
PYTHON_DEPS=
SYSTEM_DEPS=

# Root check - must be performed before any I/O redirection so sudo has direct terminal control
if [ "$EUID" -ne 0 ]; then
    echo 'Install script requires root privileges!'
    if command -v sudo >/dev/null 2>&1; then
        echo 'Switching now, enter the password for "'$USER'", if prompted.'
        exec sudo bash "$0" "$@"
    else
        echo 'Switching now, enter the password for "root"!'
        exec su root -c "bash \"$0\" $*"
    fi
    exit $?
fi

# Set up file-based logging (only after root privileges are acquired)
LOG_FILE="${INSTALL_DIR}/install.log"
exec 1> >(tee -a "$LOG_FILE")

#
# Wrapper for informational logging
# Args:
#     All arguments are written to the terminal and log file
log() {
    echo -ne "\e[1;34mlightshowpi \e[m" >&2
    echo -e "[`date`] $@"
}

#
# Checks the return value of the last command to run
# Args:
#     1 - Message to display on failure
verify() {
    if [ $? -ne 0 ]; then
        echo "Encountered a fatal error: $@"
        exit 1
    fi
}

#
# Configure installation process based on Linux distribution
install_init() {
    DISTRO=$(awk -F= '$1~/^ID$/ {print $2}' /etc/os-release | tr -d '"')
    BASE_DISTRO=$(awk -F= '$1~/^ID_LIKE$/ {print $2}' /etc/os-release | tr -d '"')

    case $DISTRO in
        archarm|raspbian|kali|debian|ubuntu)
            log Configuring installation for detected distro="'$DISTRO'"
            if [ -f "$INSTALL_DIR/install-scripts/$DISTRO" ]; then
                source "$INSTALL_DIR/install-scripts/$DISTRO"
            elif [ -f "$INSTALL_DIR/install-scripts/kali" ]; then
                source "$INSTALL_DIR/install-scripts/kali"
            else
                source "$INSTALL_DIR/install-scripts/raspbian"
            fi
            verify "Error importing configuration from install-scripts"
            ;;
        *)
            if echo "$BASE_DISTRO" | grep -qi "debian"; then
                log "Distro '$DISTRO' is Debian-based. Using Kali/Debian configuration."
                source "$INSTALL_DIR/install-scripts/kali"
                verify "Error importing configuration from install-scripts/kali"
            else
                log Detected unknown distribution. Please verify that "'$DISTRO'" is supported and update this script.
                log To add support for "'$DISTRO'" create a script with that name in "install-scripts"
                exit 1
            fi
            ;;
    esac
}

#
# Wrapper function to handle installation of system packages
# Args:
#     1 - Package name
pkginstall() {
    log Installing $1...
    $INSTALL_COMMAND $1
    verify "Installation of package '$1' failed"
}

# Pip options for PEP 668 environments (modern Debian, Kali, Ubuntu)
PIP_OPTS=""
if pip3 install --help 2>&1 | grep -q -- '--break-system-packages'; then
    PIP_OPTS="--break-system-packages"
fi
export PIP_BREAK_SYSTEM_PACKAGES=1

#
# Wrapper function to handle installation of Python packages
# Args:
#     1 - Package name
pipinstall() {
    log Installing $1 via pip...
    if [ "$1" == "numpy" ]; then echo -e "\e[1;33mWARNING:\e[m numpy installation may take up to 30 minutes"; fi
    /usr/bin/yes | pip3 install $PIP_OPTS "$1"
    verify "Installation of Python package '$1' failed"
}

# Prepare the build environment
install_init
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR && cd $BUILD_DIR

# Install system dependencies
log Preparing to install ${#SYSTEM_DEPS[@]} packages on your system...
for _dep in ${SYSTEM_DEPS[@]}; do
    pkginstall $_dep;
done

# make sure opt/vc exists (only needed on older Pi firmware, failure is not critical)
if [ ! -d /opt/vc ]; then
    log "Checking /opt/vc (optional, failure is not a concern)..."
    mkdir -p /opt/vc
fi

# WiringPi: drogon.net is deprecated; install from official community repository if not installed
if ! command -v gpio >/dev/null 2>&1; then
    log "Installing WiringPi from community repository..."
    cd /tmp
    rm -rf WiringPi
    if git clone --depth 1 https://github.com/WiringPi/WiringPi.git; then
        cd WiringPi
        ./build
        ldconfig 2>/dev/null || true
    else
        log "Warning: Failed to clone WiringPi repository."
    fi
    cd "$BUILD_DIR"
else
    log "WiringPi (gpio) is already installed."
fi

# Some symlinks that will make life a little easier
if [ -f /usr/bin/python ] && [ ! -L /usr/bin/python ] && [ "$(readlink -f /usr/bin/python 2>/dev/null)" != "$(which python3 2>/dev/null)" ]; then
    mv /usr/bin/python /usr/bin/python2 2>/dev/null || true
fi
if [ -f /usr/bin/pip ] && [ ! -L /usr/bin/pip ] && [ "$(readlink -f /usr/bin/pip 2>/dev/null)" != "$(which pip3 2>/dev/null)" ]; then
    mv /usr/bin/pip /usr/bin/pip2 2>/dev/null || true
fi
if command -v python3 >/dev/null 2>&1; then
    ln -fs "$(which python3)" /usr/bin/python
fi
if command -v pip3 >/dev/null 2>&1; then
    ln -fs "$(which pip3)" /usr/bin/pip
fi

# Install decoder
log Installing decoder...
pip3 install $PIP_OPTS --upgrade git+https://bitbucket.org/broken2048/decoder-v3.py.git
verify "Installation of decoder-1.5XB-Unix failed"

# Install Python dependencies
log Preparing to install ${#PYTHON_DEPS[@]} python packages on your system...
for _dep in "${PYTHON_DEPS[@]}"; do
    pipinstall "$_dep";
done

log Installing rpi-audio-levels...
pip3 install $PIP_OPTS git+https://bitbucket.org/broken2048/rpi-audio-levels.git
verify "Installation of rpi-audio-levels failed"

# Install pygooglevoice
log Installing pygooglevoice...
pip3 install $PIP_OPTS --upgrade git+https://github.com/pettazz/pygooglevoice.git
verify "Installation of pygooglevoice failed"

# Install wiringpipy
log Installing wiringpipy...
pip3 install $PIP_OPTS --upgrade git+https://bitbucket.org/broken2048/wiringpipy.git
verify "Installation of wiringpipy failed"

# Optionally add a line to /etc/sudoers
if [ -f /etc/sudoers ]; then
    KEEP_EN="Defaults             env_keep=\"SYNCHRONIZED_LIGHTS_HOME\""
    grep -q "$KEEP_EN" /etc/sudoers
    if [ $? -ne 0 ]; then
        echo "$KEEP_EN" >> /etc/sudoers
    fi
fi

# Set up environment variables
cat <<EOF >/etc/profile.d/lightshowpi.sh
# Lightshow Pi Home
export SYNCHRONIZED_LIGHTS_HOME=${INSTALL_DIR}
# Add Lightshow Pi bin directory to path
export PATH=\$PATH:${INSTALL_DIR}/bin
EOF

# Clean up after ourselves
cd ${INSTALL_DIR} && rm -rf ${BUILD_DIR}

# Print some instructions to the user
cat <<EOF


All done! Reboot your Raspberry Pi before running lightshowPi.
Run the following command to test your installation and hardware setup:

    sudo python $INSTALL_DIR/py/hardware_controller.py --state=flash

EOF
exit 0

