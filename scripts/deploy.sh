#!/bin/bash
# ─────────────────────────────────────────────────────────────
# NetSentinel — Deploy Script
# ─────────────────────────────────────────────────────────────
# PURPOSE:
#   Called automatically by GitHub Actions on every push to main.
#   It pulls the latest code and restarts all containers.
#
# GitHub Actions SSHs into the Oracle VM and runs this script.
# You do NOT run this manually.
# ─────────────────────────────────────────────────────────────

set -e  # Exit immediately if any command fails

echo "============================================"
echo "  NetSentinel — Deploying Latest Version..."
echo "============================================"

# ── Navigate to project directory ───────────────────────────
cd /home/$USER/NetSentinel

# ── Step 1: Pull latest code from GitHub ─────────────────────
echo ""
echo "[1/4] Pulling latest code..."
git pull origin main

# ── Step 2: Rebuild Docker images ────────────────────────────
echo ""
echo "[2/4] Rebuilding Docker images..."
cd backend
docker compose \
    -f docker-compose.yml \
    -f docker-compose.prod.yml \
    build --no-cache

# ── Step 3: Restart all containers ───────────────────────────
echo ""
echo "[3/4] Restarting containers..."
docker compose \
    -f docker-compose.yml \
    -f docker-compose.prod.yml \
    up -d --force-recreate

# ── Step 4: Clean up old unused Docker images ────────────────
echo ""
echo "[4/4] Cleaning up old images..."
docker image prune -f

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "============================================"
echo "  Deployment Complete!"
echo "  App is live at: http://$(curl -s ifconfig.me)"
echo "============================================"