#!/bin/bash

# --- CONFIGURATION ---
REPO_URL="https://github.com/Jsolsky/rpi-laser-sensor-main.git"
TARGET_DIR="/home/pi/rpi-laser-sensor-main"
SERVER_SCRIPT="server.py"
# ---------------------

# 1. Wait for internet connection (Crucial for Pi boot)
echo "Waiting for internet..."
until ping -c 1 8.8.8.8 &> /dev/null; do
    sleep 5
done

# 2. Clone or Update
if [ ! -d "$TARGET_DIR" ]; then
    echo "Cloning repository..."
    git clone $REPO_URL $TARGET_DIR
else
    echo "Directory exists. Pulling latest changes..."
    cd $TARGET_DIR
    git pull
fi

# 3. Handle Dependencies
# It is highly recommended to use a Virtual Environment (venv) 
# to avoid breaking system-wide Python packages.
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Updating dependencies..."
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
sudo apt install python3-picamera2

#4. Launch Server
cd $TARGET_DIR

echo "Launching server.py..."
# Using 'exec' ensures the shell hands over the process to Python 
# This makes systemd tracking much more accurate
exec /usr/bin/python3 $SERVER_SCRIPT
# exec /usr/bin/python3 $SERVER_SCRIPT >> /home/pi/server_log.txt 2>&1