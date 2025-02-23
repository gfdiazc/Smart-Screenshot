#!/bin/bash
set -e  # Exit on error

echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo "Installing Playwright..."
python3 -m pip install --upgrade "playwright[chromium]==1.42.0"

echo "Installing Playwright dependencies..."
playwright install-deps

echo "Installing Chromium..."
playwright install chromium

echo "Verifying installation..."
python3 -c "from playwright.sync_api import sync_playwright; print('Playwright installation verified')"

echo "Setup completed successfully!"