#!/bin/bash

# --- CONFIGURATION ---
REPO_URL="https://github.com/Jsolsky/rpi-laser-sensor-main.git"
TARGET_DIR="/home/pi/rpi-laser-sensor-main"
SERVER_SCRIPT="server.py"
# ---------------------

# 1. Wait for internet connection
echo "Waiting for internet..."
until ping -c 1 8.8.8.8 &> /dev/null; do
    sleep 5
done

# 2. Clone or Update
if [ ! -d "$TARGET_DIR" ]; then
    echo "Cloning repository..."
    git clone "$REPO_URL" "$TARGET_DIR"
    cd "$TARGET_DIR" || exit
else
    echo "Directory exists. Pulling latest changes..."
    cd "$TARGET_DIR" || exit
    git pull
fi

sudo apt install -y python3-picamera2

# CRITICAL: Ensure the system-level library is actually there
echo "Ensuring system-level picamera2 is installed..."
sudo apt update
sudo apt install -y python3-picamera2

# 3. Handle Virtual Environment
# FORCE RECREATION: If you still have errors, delete the 'venv' folder manually once: 
# rm -rf /home/pi/rpi-laser-sensor-main/venv
if [ ! -d "venv" ]; then
    echo "Creating NEW virtual environment with system access..."
    python3 -m venv --system-site-packages venv
else
    echo "Venv exists. Note: If errors persist, delete the venv folder and run again."
fi

# Activate the venv
echo "Activating virtual environment..."
source venv/bin/activate

# 4. Install Dependencies
# We use pip inside the venv instead of apt to keep the system clean
if [ -f "requirements.txt" ]; then
    echo "Installing/Updating python dependencies via pip..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# 5. Launch Server
echo "Launching $SERVER_SCRIPT..."

# Use the python executable located INSIDE the venv
# This ensures all dependencies are loaded correctly
exec "$TARGET_DIR/venv/bin/python3" "$TARGET_DIR/$SERVER_SCRIPT"