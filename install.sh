#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo -e "\n🚀 Installing Flow: Zero-Latency Dictation Daemon...\n"

# 1. System Dependencies (Arch specific)
echo "📦 Installing system dependencies via pacman..."
# --needed prevents reinstalling packages you already have
sudo pacman -S --needed portaudio xdotool xclip pulseaudio-alsa libpulse python-numpy python-sounddevice python-pynput python-pip

# 2. Environment Paths
REPO_DIR=$(pwd)
VENV_DIR="$REPO_DIR/venv"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/wispr-clone.service"

# 3. Virtual Environment Setup
echo -e "\n🐍 Setting up Python virtual environment..."
# We use --system-site-packages to leverage pacman's numpy and sounddevice
python3 -m venv "$VENV_DIR" --system-site-packages

echo "📥 Installing faster-whisper via pip..."
"$VENV_DIR/bin/pip" install faster-whisper==1.0.1

# 4. Systemd Service Generation
echo -e "\n⚙️ Generating systemd service file..."
mkdir -p "$SERVICE_DIR"

# Dynamically write the service file pointing to the current cloned directory
cat <<EOF >"$SERVICE_FILE"
[Unit]
Description=Flow Dictation Daemon
After=graphical-session.target pipewire.service
   
[Service]
Type=simple
Environment="DISPLAY=:0"
Environment="XAUTHORITY=%h/.Xauthority" 
   
ExecStart=$VENV_DIR/bin/python $REPO_DIR/flow.py
   
Restart=on-failure
RestartSec=3
   
[Install]
WantedBy=default.target
EOF

# 5. Enable and Start the Daemon
echo -e "\n🔄 Reloading systemd..."
systemctl --user daemon-reload

echo "▶️ Enabling and starting the background service..."
systemctl --user enable --now wispr-clone.service

echo -e "\n✅ Installation complete!"
echo -e "🎙️  Flow is now running silently in the background."
echo -e "   - Hold Super + Shift to dictate."
echo -e "   - Check live logs: journalctl --user -u wispr-clone.service -f\n"
