#!/bin/bash
# ─────────────────────────────────────────────────────────────
# NetSentinel — Oracle VM Server Setup Script
# ─────────────────────────────────────────────────────────────
# PURPOSE:
#   Run this ONCE on your Oracle VM after first login.
#   It installs Docker, Docker Compose, and prepares the server.
#
# HOW TO RUN (on your Oracle VM via SSH):
#   chmod +x server-setup.sh
#   ./server-setup.sh
# ─────────────────────────────────────────────────────────────

set -e  # Exit immediately if any command fails

echo "============================================"
echo "  NetSentinel — Server Setup Starting..."
echo "============================================"

# ── Step 1: Update system packages ──────────────────────────
echo ""
echo "[1/7] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# ── Step 2: Install required dependencies ───────────────────
echo ""
echo "[2/7] Installing dependencies..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw

# ── Step 3: Install Docker ───────────────────────────────────
echo ""
echo "[3/7] Installing Docker..."

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update -y
sudo apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# ── Step 4: Add current user to docker group ─────────────────
echo ""
echo "[4/7] Adding user to docker group..."
sudo usermod -aG docker $USER
echo "NOTE: You will need to log out and back in for this to take effect."

# ── Step 5: Enable Docker to start on boot ───────────────────
echo ""
echo "[5/7] Enabling Docker on startup..."
sudo systemctl enable docker
sudo systemctl start docker

# ── Step 6: Configure firewall (UFW) ─────────────────────────
echo ""
echo "[6/7] Configuring firewall..."

# Allow SSH (port 22) — IMPORTANT: always keep this open
sudo ufw allow 22/tcp

# Allow HTTP (port 80) — for your app
sudo ufw allow 80/tcp

# Allow HTTPS (port 443) — for future SSL
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw --force enable

echo "Firewall rules set: SSH(22), HTTP(80), HTTPS(443) allowed."

# ── Step 7: Clone the NetSentinel repository ─────────────────
echo ""
echo "[7/7] Cloning NetSentinel repository..."

# IMPORTANT: Replace this URL with your actual GitHub repo URL
REPO_URL="https://github.com/Asma123-tech/NetSentinel.git"

if [ -d "/home/$USER/NetSentinel" ]; then
    echo "Repository already exists. Pulling latest changes..."
    cd /home/$USER/NetSentinel
    git pull
else
    git clone $REPO_URL /home/$USER/NetSentinel
    echo "Repository cloned successfully."
fi

# ── Setup .env file ──────────────────────────────────────────
echo ""
echo "─────────────────────────────────────────────"
echo "  MANUAL STEP REQUIRED:"
echo "─────────────────────────────────────────────"
echo ""
echo "  You must create your .env file on the server:"
echo ""
echo "  cd /home/$USER/NetSentinel/backend"
echo "  cp .env.example .env"
echo "  nano .env"
echo ""
echo "  Fill in these values in .env:"
echo "    DATABASE_URL      — use your DB password"
echo "    FRONTEND_ORIGIN   — your Oracle VM public IP"
echo "    JWT_SECRET_KEY    — generate with:"
echo "                        openssl rand -hex 32"
echo ""
echo "─────────────────────────────────────────────"
echo ""
echo "============================================"
echo "  Setup Complete!"
echo "  Please log out and log back in, then run:"
echo "  cd NetSentinel/backend"
echo "  docker compose -f docker-compose.yml \\"
echo "    -f docker-compose.prod.yml up -d"
echo "============================================"