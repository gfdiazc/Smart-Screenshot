#!/bin/bash
set -e  # Exit on error

echo "Updating system package list..."
apt-get update

echo "Installing system dependencies..."
apt-get install -y wget curl unzip fontconfig locales gstreamer1.0-libav \
    libnss3-dev libxss1 libasound2 libxrandr2 libatk1.0-0 libatk-bridge2.0-0 \
    libpangocairo-1.0-0 libgtk-3-0 libgbm1 libxshmfence1 libegl1

echo "Installing Chromium..."
# Intentar instalar con apt
apt-get install -y chromium chromium-browser || {
    echo "Failed to install Chromium with apt, trying snap..."
    apt-get install -y snapd
    snap install chromium
}

echo "Setting up environment variables..."
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
export PYTHONPATH="${PYTHONPATH}:/usr/lib/chromium:/usr/lib/chromium-browser:/snap/bin"

echo "Creating symbolic links..."
# Crear enlaces simbólicos para todas las posibles ubicaciones
for source in "/usr/bin/chromium-browser" "/snap/bin/chromium" "/usr/lib/chromium/chromium"; do
    if [ -f "$source" ]; then
        echo "Found Chromium at $source"
        ln -sf "$source" /usr/bin/chromium 2>/dev/null || true
        ln -sf "$source" /usr/bin/chrome 2>/dev/null || true
        break
    fi
done

echo "Verifying Chromium installation..."
which chromium || which chromium-browser || which chrome || {
    echo "ERROR: No Chromium executable found!"
    exit 1
}

echo "Checking Chromium version..."
(chromium --version || chromium-browser --version || chrome --version) || {
    echo "ERROR: Could not determine Chromium version!"
    exit 1
}

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
    try:
        browser = p.chromium.launch()
        print('Launching browser: OK')
        browser.close()
        print('Closing browser: OK')
    except Exception as e:
        print(f'Error launching browser: {e}')
        print('Trying with system Chromium...')
        for path in ['/usr/bin/chromium-browser', '/usr/bin/chromium', '/usr/bin/chrome', '/snap/bin/chromium']:
            if os.path.exists(path):
                print(f'Found Chromium at: {path}')
                browser = p.chromium.launch(executable_path=path)
                print('Launching browser with system Chromium: OK')
                browser.close()
                print('Closing browser: OK')
                break
"

echo "Setup completed successfully!"