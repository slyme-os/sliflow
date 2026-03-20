#!/usr/bin/env bash

echo -e "\n🧹 Uninstalling Flow Dictation Daemon...\n"

# Define paths
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/wispr-clone.service"
REPO_DIR=$(pwd)
VENV_DIR="$REPO_DIR/venv"

# 1. Stop and Disable Service
# Using || true ensures the script doesn't crash if the service is already stopped
echo "⏹️  Stopping and disabling systemd service..."
systemctl --user stop wispr-clone.service 2>/dev/null || true
systemctl --user disable wispr-clone.service 2>/dev/null || true

# 2. Remove Service File
if [ -f "$SERVICE_FILE" ]; then
  echo "🗑️  Removing systemd service file..."
  rm "$SERVICE_FILE"

  echo "🔄 Reloading systemd daemon..."
  systemctl --user daemon-reload
else
  echo "⏭️  Systemd service file not found, skipping..."
fi

# 3. Remove Virtual Environment
if [ -d "$VENV_DIR" ]; then
  echo "🗑️  Removing Python virtual environment..."
  rm -rf "$VENV_DIR"
else
  echo "⏭️  Virtual environment not found, skipping..."
fi

echo -e "\n✅ Uninstallation complete!"
echo -e "ℹ️  Note: The Whisper AI model weights (~600MB) are still cached on your system."
echo -e "   If you want to completely free up that disk space, run:"
echo -e "   rm -rf ~/.cache/huggingface/hub/\n"
