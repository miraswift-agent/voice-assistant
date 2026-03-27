#!/bin/bash
# Setup desktop launcher for voice assistant

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$SCRIPT_DIR/voice-assistant.desktop"
DESKTOP_DIR="$HOME/Desktop"

echo "Setting up Voice Assistant desktop launcher..."

# Create Desktop directory if it doesn't exist
mkdir -p "$DESKTOP_DIR"

# Copy launcher to desktop
cp "$DESKTOP_FILE" "$DESKTOP_DIR/"

# Make it executable
chmod +x "$DESKTOP_DIR/voice-assistant.desktop"

# Mark as trusted (required on some desktop environments)
gio set "$DESKTOP_DIR/voice-assistant.desktop" metadata::trusted true 2>/dev/null || true

echo "✓ Desktop launcher installed at: $DESKTOP_DIR/voice-assistant.desktop"
echo ""
echo "You should now see a 'Voice Assistant' icon on your desktop."
echo "Double-click it to start the voice assistant GUI."
