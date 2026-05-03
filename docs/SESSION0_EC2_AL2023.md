# Session 0 — EC2 + Amazon Linux 2023 (quick checklist)

Use this when **NIM + Session 1** run on **the same EC2 instance** (no Windows Docker Desktop).

---

## A. Instance + driver

1. [ ] Instance type with enough GPU VRAM for your NIM (e.g. **`g6e.xlarge`** = 1× L40S 48 GB).
2. [ ] **Amazon Linux 2023** (GPU / DLAMI recommended so **`nvidia-smi`** works immediately).
3. [ ] After boot: `nvidia-smi` shows GPU + driver.

If `nvidia-smi` fails, install the driver per [NVIDIA drivers for AL2023](https://docs.aws.amazon.com/linux/al2023/ug/nvidia-drivers.html) or use a **GPU AMI**, then **reboot**.

---

## B. Docker + NVIDIA Container Toolkit

1. [ ] `sudo dnf install -y docker && sudo systemctl enable --now docker`
2. [ ] `sudo usermod -aG docker ec2-user` → **log out and back in**
3. [ ] Add NVIDIA repo + install toolkit:

   ```bash
   curl -fsSL https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
     sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
   sudo dnf install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

4. [ ] Test: `docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubi8 nvidia-smi`

If you see **`libnvidia-ml.so.1`**: the **host driver** is missing or broken — fix **A** before **B**.

---

## C. NGC + NIM

1. [ ] `echo "$NGC_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin`
2. [ ] Run your NIM `docker run ...` (cache volume, `-p 8000:8000`, etc.)
3. [ ] On the instance: `curl -s http://127.0.0.1:8000/v1/models`

---

## D. Python 3.12 on Amazon Linux 2023

AL2023 keeps **`/usr/bin/python3`** on **Python 3.9** for OS tools (`dnf`, `cloud-init`, etc.). **Do not** replace that symlink. Install **3.12** alongside and call it explicitly.

### Install

```bash
sudo dnf install -y python3.12 python3.12-pip
```

Optional (only if you build C extensions / some wheels):

```bash
sudo dnf install -y python3.12-devel gcc
```

### Use 3.12

```bash
python3.12 --version
python3.12 -m pip --version
```

Install packages with:

```bash
python3.12 -m pip install ...
# or, if the shim exists:
pip3.12 install ...
```

### venv (recommended for this repo)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

After `activate`, `python` and `pip` inside `.venv` are 3.12.

**Official doc:** [Python in AL2023](https://docs.aws.amazon.com/linux/al2023/ug/python.html) (multiple versions, `python3.12`, and why system `python3` stays 3.9).

---

## E. Python venv for **this repo** (inference only — no PyTorch)

From the cloned `nvidia-demo` root (after **D**):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-ec2-inference.txt
```

Or: `bash scripts/setup_ec2_venv.sh` (set `PYTHON=python3.12` if your default `python3` is not 3.12).

1. [ ] `export SESSION0_EC2=1` then `python scripts/check_env.py` (skips PyTorch; checks agent libs + optional NIM URL).

---

## F. Session 1 on EC2

1. [ ] Copy `.env.example` → `.env` with `OPENAI_BASE_URL=http://127.0.0.1:8000/v1` (same host as NIM) and **`OPENAI_MODEL`** from `/v1/models`.
2. [ ] `source .venv/bin/activate && python scripts/run_session1.py`

**Security group:** only open **8000** to your IP if you must hit NIM from outside; for **localhost-only**, default SG is fine.

---

## Link to Windows laptop path

[SESSION0_LLM_WINDOWS.md](SESSION0_LLM_WINDOWS.md) — PowerShell + Docker Desktop when developing on Windows.
