#!/usr/bin/env bash
# =============================================================================
# Automated Production Deployment Script for Delta EMA 120 Trading Bot
# Compatible with Ubuntu 22.04 / 24.04 LTS
# =============================================================================

set -e

echo "=== Delta Exchange EMA 120 Trading Bot Production Deployment ==="

# 1. Update system packages
echo "[1/4] Updating Linux system packages..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git ufw

# 2. Check and install Docker & Docker Compose if not present
if ! command -v docker &> /dev/null; then
    echo "[2/4] Installing Docker and Docker Compose plugin..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker "$USER"
    rm get-docker.sh
else
    echo "[2/4] Docker is already installed."
fi

# 3. Configure Firewall (UFW)
echo "[3/4] Configuring firewall ports (SSH 22, HTTP 80, HTTPS 443)..."
sudo ufw allow 22/tcp || true
sudo ufw allow 80/tcp || true
sudo ufw allow 443/tcp || true
sudo ufw --force enable || true

# 4. Build and start containers
echo "[4/4] Building and starting Docker containers in detached mode..."
docker compose pull || true
docker compose build --no-cache
docker compose up -d

echo ""
echo "=== Deployment Complete! ==="
echo "Frontend:  http://$(curl -s ifconfig.me)"
echo "Backend:   http://$(curl -s ifconfig.me):8000"
echo "API Docs:  http://$(curl -s ifconfig.me):8000/docs"
echo ""
echo "To monitor live logs run: docker compose logs -f backend"
