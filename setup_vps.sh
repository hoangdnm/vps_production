#!/bin/bash

# VPS Production Deployment Script
echo "=== TRADING API VPS PRODUCTION DEPLOYMENT ==="

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python3 and pip
echo "Installing Python3 and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y curl build-essential

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv vps_env
source vps_env/bin/activate

# Install Python packages
echo "Installing Python packages..."
pip install -r requirements.txt

# Create directories
mkdir -p logs
mkdir -p backups

# Set permissions
chmod +x *.sh

echo "=== VPS SETUP COMPLETE ==="
echo "Next steps:"
echo "1. Start data collector: ./start_data_collector.sh"
echo "2. Start API server: ./start_api_server.sh"
echo "3. Setup systemd service: ./setup_systemd.sh"
