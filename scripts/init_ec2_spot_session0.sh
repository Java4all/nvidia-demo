#!/usr/bin/env bash
# =============================================================================
# Session 0 — EC2 Spot / GPU instance bootstrap (Amazon Linux 2023)
#
# Defines "Session 0 on EC2" as in docs/SESSION0_EC2_AL2023.md:
#   A. GPU driver (use GPU AMI / DLAMI — not installed here)
#   B. Docker + NVIDIA Container Toolkit
#   C. NGC login + NIM — you run manually (needs NGC_API_KEY)
#   D–E. Python 3.12 + repo venv (inference stack, no PyTorch)
#   F. Session 1 prep — clone repo, .env from example, then run_session1.py
#
# Data volume: second EBS/NVMe disk for Docker + NIM cache + optional repo.
# On Nitro, console device /dev/sdb often appears as /dev/nvme1n1 — override
# with DATA_DEVICE if needed.
#
# Usage (instance user-data or SSH as root):
#   curl -fsSL https://raw.githubusercontent.com/.../init_ec2_spot_session0.sh | sudo bash
# Or copy to the instance and:
#   sudo bash init_ec2_spot_session0.sh
#
# Environment (optional):
#   DATA_DEVICE=/dev/nvme1n1   # block device to format+mount (default: auto)
#   MOUNT_POINT=/data          # mount point (default /data)
#   NV_DEMO_REPO_URL=...      # if set: git clone into $MOUNT_POINT/nvidia-demo
#   NV_DEMO_BRANCH=main
#   SKIP_DOCKER=1             # skip Docker + nvidia-container-toolkit
#   SKIP_VENV=1               # skip Python venv (no clone or no repo dir)
#   WAIT_FOR_VOLUME_SECS=15   # delay before auto-detect disk (user-data vs attach race); 0=skip
# =============================================================================
set -euo pipefail

log() { echo "[session0-init] $*"; }

MOUNT_POINT="${MOUNT_POINT:-/data}"
DATA_DEVICE="${DATA_DEVICE:-}"
WAIT_FOR_VOLUME_SECS="${WAIT_FOR_VOLUME_SECS:-15}"
NV_DEMO_REPO_URL="${NV_DEMO_REPO_URL:-}"
NV_DEMO_BRANCH="${NV_DEMO_BRANCH:-main}"
SKIP_DOCKER="${SKIP_DOCKER:-0}"
SKIP_VENV="${SKIP_VENV:-0}"

if [[ "$(id -u)" -ne 0 ]]; then
  log "re-run with sudo"
  exit 1
fi

if [[ -z "$DATA_DEVICE" && "${WAIT_FOR_VOLUME_SECS}" != "0" ]]; then
  log "sleep ${WAIT_FOR_VOLUME_SECS}s for volume attach (WAIT_FOR_VOLUME_SECS=0 to skip)"
  sleep "$WAIT_FOR_VOLUME_SECS"
fi

root_part="$(findmnt -n -o SOURCE / 2>/dev/null || true)"
root_disk=""
if [[ -n "$root_part" ]]; then
  root_disk="$(lsblk -ndo PKNAME "$root_part" 2>/dev/null || true)"
fi

pick_data_device() {
  if [[ -n "$DATA_DEVICE" ]]; then
    if [[ ! -b "$DATA_DEVICE" ]]; then
      log "DATA_DEVICE=$DATA_DEVICE is not a block device"
      exit 1
    fi
    echo "$DATA_DEVICE"
    return
  fi
  local candidates=(/dev/nvme1n1 /dev/nvme2n1 /dev/sdb /dev/xvdb)
  for c in "${candidates[@]}"; do
    [[ -b "$c" ]] || continue
    local pk=""
    pk="$(lsblk -ndo PKNAME "$c" 2>/dev/null || true)"
    # Whole-disk candidate: PKNAME empty; partition candidate: compare parents
    local base
    base="$(basename "$c")"
    if [[ "$base" == "$root_disk" ]]; then
      continue
    fi
    if [[ -n "$pk" && "$pk" == "$root_disk" ]]; then
      continue
    fi
    echo "$c"
    return
  done
  log "No secondary disk found. Attach a volume or set DATA_DEVICE= (root_disk=${root_disk:-unknown})"
  exit 1
}

DEV="$(pick_data_device)"
log "using data device: $DEV -> $MOUNT_POINT"

if ! command -v mkfs.xfs >/dev/null 2>&1; then
  dnf install -y xfsprogs
fi

mkdir -p "$MOUNT_POINT"

existing_fs="$(blkid -o value -s TYPE "$DEV" 2>/dev/null || true)"
if [[ -z "$existing_fs" ]]; then
  log "formatting $DEV as xfs"
  mkfs.xfs -f -L nvdemodata "$DEV"
elif [[ "$existing_fs" != xfs ]]; then
  log "device $DEV has type=$existing_fs (expected empty or xfs). Set DATA_DEVICE or reformat manually."
  exit 1
else
  log "existing xfs on $DEV — skipping mkfs"
fi

UUID="$(blkid -s UUID -o value "$DEV")"
if ! grep -qE "^UUID=${UUID}[[:space:]]" /etc/fstab 2>/dev/null; then
  echo "UUID=$UUID $MOUNT_POINT xfs defaults,nofail 0 2" >>/etc/fstab
  log "added fstab entry for UUID=$UUID"
fi
mount -a
log "mounted $MOUNT_POINT ($(df -h "$MOUNT_POINT" | tail -1))"

DOCKER_DATA_ROOT="$MOUNT_POINT/docker"
mkdir -p "$DOCKER_DATA_ROOT"

log "dnf: base packages"
dnf install -y git curl gcc python3.12 python3.12-pip python3.12-devel

if [[ "$SKIP_DOCKER" != "1" ]]; then
  log "dnf: docker"
  dnf install -y docker
  systemctl stop docker 2>/dev/null || true

  mkdir -p /etc/docker
  export DOCKER_DATA_ROOT
  python3 <<'PY'
import json, os
path = "/etc/docker/daemon.json"
root = os.environ["DOCKER_DATA_ROOT"]
data = {}
if os.path.isfile(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = {}
data["data-root"] = root
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
  log "Docker data-root -> $DOCKER_DATA_ROOT (/etc/docker/daemon.json)"

  systemctl enable docker
  systemctl start docker
  usermod -aG docker ec2-user || true

  if [[ ! -f /etc/yum.repos.d/nvidia-container-toolkit.repo ]]; then
    log "nvidia-container-toolkit repo"
    curl -fsSL https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo |
      tee /etc/yum.repos.d/nvidia-container-toolkit.repo >/dev/null
  fi
  dnf install -y nvidia-container-toolkit
  nvidia-ctk runtime configure --runtime=docker
  systemctl restart docker
  log "Docker + NVIDIA Container Toolkit configured"
else
  log "SKIP_DOCKER=1 — skipping Docker / toolkit"
fi

# NIM / model cache on data volume
mkdir -p "$MOUNT_POINT/nim-cache"
chmod 777 "$MOUNT_POINT/nim-cache" 2>/dev/null || true

REPO_DIR="$MOUNT_POINT/nvidia-demo"
if [[ -n "$NV_DEMO_REPO_URL" ]]; then
  if [[ ! -d "$REPO_DIR/.git" ]]; then
    log "cloning $NV_DEMO_REPO_URL (branch $NV_DEMO_BRANCH)"
    rm -rf "$REPO_DIR"
    git clone --branch "$NV_DEMO_BRANCH" --depth 1 "$NV_DEMO_REPO_URL" "$REPO_DIR"
    chown -R ec2-user:ec2-user "$REPO_DIR" 2>/dev/null || true
  else
    log "repo already present at $REPO_DIR"
  fi
else
  log "NV_DEMO_REPO_URL unset — clone nvidia-demo to $REPO_DIR manually or export and re-run"
fi

if [[ "$SKIP_VENV" != "1" && -f "$REPO_DIR/scripts/setup_ec2_venv.sh" ]]; then
  log "Python 3.12 venv (requirements-ec2-inference.txt)"
  sudo -u ec2-user bash -c "cd '$REPO_DIR' && PYTHON=python3.12 bash scripts/setup_ec2_venv.sh"
elif [[ "$SKIP_VENV" == "1" ]]; then
  log "SKIP_VENV=1 — skipping venv"
else
  log "no repo at $REPO_DIR — skipping venv (copy repo or set NV_DEMO_REPO_URL)"
fi

cat <<EOF

================================================================================
Session 0 (EC2) bootstrap finished.
  Data volume: $DEV -> $MOUNT_POINT
  Docker data-root: $DOCKER_DATA_ROOT (see /etc/docker/daemon.json)

Next (operator):
  1) nvidia-smi   # confirm GPU driver (AMI); reboot if you had to install driver
  2) Log out/in as ec2-user so 'docker' group applies
  3) NGC:  echo "\$NGC_API_KEY" | docker login nvcr.io --username '\$oauthtoken' --password-stdin
  4) Run NIM with a cache mount, e.g.  -v $MOUNT_POINT/nim-cache:/opt/nim/.cache  (see your NIM doc)
  5) cd $REPO_DIR && source .venv/bin/activate
     cp -n .env.example .env   # set OPENAI_BASE_URL=http://127.0.0.1:8000/v1 and OPENAI_MODEL
     SESSION0_EC2=1 python scripts/check_env.py
     python scripts/run_session1.py

Session 0 definition: inference node = Docker+NIM + Python agent deps (no PyTorch);
  SESSION0_EC2=1 matches docs/SESSION0_EC2_AL2023.md sections B–E.
================================================================================
EOF
