#!/bin/bash

# Make the start script executable
chmod +x "$(dirname "$0")/start_ekospex.sh"

# Get the absolute path of the current directory
EKO_DIR="$(cd "$(dirname "$0")" && pwd)"

# Update the service file with the correct path
sed -i "s|/home/pi/ekospex|$EKO_DIR|g" "$EKO_DIR/ekospex.service"

# Copy the service file to the systemd directory
sudo cp "$EKO_DIR/ekospex.service" /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start at boot
sudo systemctl enable ekospex.service

# Start the service now
sudo systemctl start ekospex.service

echo "Ekospex service has been installed and started."
echo "You can check its status with: sudo systemctl status ekospex.service"
echo "You can stop it with: sudo systemctl stop ekospex.service"
echo "You can restart it with: sudo systemctl restart ekospex.service" 