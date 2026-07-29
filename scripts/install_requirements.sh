#!/usr/bin/env bash
# -----------------------------------------------------------------------
# Install the host requirements for the EPICS Lab stack:
#
#   - Docker Engine + Compose v2 plugin + Buildx (from Docker's official
#     repository, so `docker compose` works)
#   - git, GNU make, curl, python3
#
# Supported: Debian/Ubuntu (apt), Fedora/RHEL/Rocky/Alma (dnf).
# Idempotent — already-installed components are skipped.
#
# Usage:
#   sudo ./scripts/install_requirements.sh [--yes]
#
#   --yes   non-interactive (assume "yes" to the confirmation prompt)
# -----------------------------------------------------------------------
set -euo pipefail

ASSUME_YES=0
[ "${1:-}" = "--yes" ] || [ "${1:-}" = "-y" ] && ASSUME_YES=1

info()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33mWARNING:\033[0m %s\n' "$*" >&2; }
die()   { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# ------------------------------------------------------------- preflight
[ "$(id -u)" -eq 0 ] || die "run as root, e.g.: sudo $0"

# The user who invoked sudo (added to the docker group at the end).
TARGET_USER="${SUDO_USER:-}"

[ -r /etc/os-release ] || die "cannot detect distribution (/etc/os-release missing)"
. /etc/os-release
DISTRO_ID="${ID:-unknown}"
DISTRO_LIKE="${ID_LIKE:-}"

case "$DISTRO_ID $DISTRO_LIKE" in
    *debian*|*ubuntu*) PKG=apt ;;
    *fedora*|*rhel*|*centos*) PKG=dnf ;;
    *) die "unsupported distribution '$DISTRO_ID' — install Docker Engine + \
Compose v2, git, and make manually (see https://docs.docker.com/engine/install/)" ;;
esac

info "Detected: ${PRETTY_NAME:-$DISTRO_ID} (package manager: $PKG)"
echo "This will install: Docker Engine + Compose v2 + Buildx, git, make, curl, python3"
if [ "$ASSUME_YES" -ne 1 ]; then
    read -r -p "Continue? [y/N] " reply
    case "$reply" in [Yy]*) ;; *) echo "Aborted."; exit 1 ;; esac
fi

# ------------------------------------------------------- base utilities
install_base_apt() {
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y ca-certificates curl git make python3 gnupg
}

install_base_dnf() {
    dnf install -y ca-certificates curl git make python3 dnf-plugins-core
}

# ------------------------------------------------------- docker engine
docker_ok() {
    command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1
}

install_docker_apt() {
    # Docker's official apt repository (docker.io/podman lack Compose v2).
    install -m 0755 -d /etc/apt/keyrings
    if [ ! -f /etc/apt/keyrings/docker.asc ]; then
        curl -fsSL "https://download.docker.com/linux/${DISTRO_ID}/gpg" \
            -o /etc/apt/keyrings/docker.asc
        chmod a+r /etc/apt/keyrings/docker.asc
    fi
    # shellcheck source=/dev/null
    codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-$(lsb_release -cs 2>/dev/null || true)}")"
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/${DISTRO_ID} ${codename} stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
}

install_docker_dnf() {
    repo_os="$DISTRO_ID"
    case "$DISTRO_ID" in
        rocky|almalinux|rhel) repo_os=rhel ;;
        centos) repo_os=centos ;;
        fedora) repo_os=fedora ;;
    esac
    dnf config-manager --add-repo \
        "https://download.docker.com/linux/${repo_os}/docker-ce.repo" 2>/dev/null \
        || dnf-3 config-manager --add-repo \
        "https://download.docker.com/linux/${repo_os}/docker-ce.repo"
    dnf install -y docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
}

info "Installing base utilities (git, make, curl, python3)..."
"install_base_${PKG}"

if docker_ok; then
    info "Docker Engine + Compose v2 already installed — skipping."
else
    info "Installing Docker Engine + Compose v2..."
    "install_docker_${PKG}"
fi

# ---------------------------------------------------------- post-install
info "Enabling and starting the Docker service..."
systemctl enable --now docker 2>/dev/null || warn "systemd not available — start dockerd manually"

if [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
    if id -nG "$TARGET_USER" | tr ' ' '\n' | grep -qx docker; then
        info "User '$TARGET_USER' is already in the docker group."
    else
        info "Adding user '$TARGET_USER' to the docker group..."
        usermod -aG docker "$TARGET_USER"
        NEEDS_RELOGIN=1
    fi
fi

# ---------------------------------------------------------------- verify
info "Versions:"
docker --version
docker compose version
docker buildx version | head -1
git --version
make --version | head -1
python3 --version

echo
info "Host requirements installed."
if [ "${NEEDS_RELOGIN:-0}" -eq 1 ]; then
    warn "Log out and back in (or run 'newgrp docker') so '$TARGET_USER' can use Docker without sudo."
fi
echo "Next steps:"
echo "  cp .env.example .env"
echo "  make build && make up && make bootstrap && make test"
