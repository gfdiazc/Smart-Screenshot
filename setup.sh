#!/bin/bash
set -e  # Exit on error

echo "Updating system package list..."
apt-get update

echo "Installing system dependencies..."
apt-get install -y wget curl unzip fontconfig locales gstreamer1.0-libav \
    libnss3-dev libxss1 libasound2 libxrandr2 libatk1.0-0 libatk-bridge2.0-0 \
    libpangocairo-1.0-0 libgtk-3-0 libgbm1 libxshmfence1 libegl1 \
    chromium chromium-browser

echo "Setting up environment variables..."
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
export PYTHONPATH="${PYTHONPATH}:/usr/lib/chromium"
export CHROME_EXECUTABLE_PATH=/usr/bin/chromium-browser

echo "Creating symbolic links..."
ln -sf /usr/bin/chromium-browser /usr/bin/chromium
ln -sf /usr/bin/chromium-browser /usr/bin/chrome

echo "Verifying Chromium installation..."
which chromium-browser
chromium-browser --version

echo "Upgrading pip..."
python3 -m pip install --upgrade pip setuptools wheel

echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt

echo "Verifying Playwright installation..."
python3 -c "
from playwright.sync_api import sync_playwright
print('Importing Playwright: OK')
with sync_playwright() as p:
    print('Creating Playwright instance: OK')
    browser = p.chromium.launch(executable_path='/usr/bin/chromium-browser')
    print('Launching browser: OK')
    browser.close()
    print('Closing browser: OK')
"

echo "Setup completed successfully!"