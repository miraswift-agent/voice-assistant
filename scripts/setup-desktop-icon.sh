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

# Mark as trusted (multiple methods for compatibility)
# Method 1: gio (GNOME/modern desktops)
gio set "$DESKTOP_DIR/voice-assistant.desktop" metadata::trusted true 2>/dev/null || true

# Method 2: xdg-desktop-menu (alternative)
xdg-desktop-menu install --novendor "$DESKTOP_DIR/voice-assistant.desktop" 2>/dev/null || true

# Method 3: Set the executable bit (Raspberry Pi OS specific)
chmod 755 "$DESKTOP_DIR/voice-assistant.desktop"

# Method 4: Create a wrapper script (most reliable)
cat > "$HOME/voice-assistant/launch.sh" << 'LAUNCHER'
#!/bin/bash
cd ~/voice-assistant
source venv/bin/activate
python src/voice_assistant_gui.py
LAUNCHER

chmod +x "$HOME/voice-assistant/launch.sh"

# Update desktop file to use wrapper
sed -i "s|^Exec=.*|Exec=$HOME/voice-assistant/launch.sh|" "$DESKTOP_DIR/voice-assistant.desktop"

echo "✓ Desktop launcher installed at: $DESKTOP_DIR/voice-assistant.desktop"
echo "✓ Wrapper script created at: $HOME/voice-assistant/launch.sh"
echo ""
echo "The icon should now launch directly without prompts."
echo "If you still get a prompt, right-click the icon and select 'Trust this executable'."
