#!/bin/bash
set -e  # Exit on error

echo "Updating system package list..."
apt-get update

echo "Installing system dependencies..."
apt-get install -y chromium chromium-browser

echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo "Installing Python dependencies..."
python3 -m pip install --upgrade "playwright==1.42.0"

echo "Setting up Playwright..."
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

echo "Verifying installation..."
python3 -c "from playwright.sync_api import sync_playwright; print('Playwright installation verified')"

echo "Setup completed successfully!"