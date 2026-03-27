#!/bin/bash
# Download required models for voice assistant

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_ROOT/models"

echo "📦 Downloading voice models..."
mkdir -p "$MODELS_DIR"

# Download Piper TTS model (en_US-lessac-medium)
echo "Downloading Piper TTS model..."
cd "$MODELS_DIR"

if [ ! -f "en_US-lessac-medium.onnx" ]; then
    wget -q --show-progress \
        https://github.com/rhasspy/piper/releases/download/v1.2.0/voice-en_US-lessac-medium.tar.gz \
        -O voice-en_US-lessac-medium.tar.gz
    
    tar -xzf voice-en_US-lessac-medium.tar.gz
    mv en_US-lessac-medium.onnx* .
    rm -rf voice-en_US-lessac-medium.tar.gz en_US-lessac-medium/
    
    echo "✓ Piper TTS model downloaded"
else
    echo "✓ Piper TTS model already exists"
fi

# Download wake word models (openwakeword downloads automatically on first run)
echo ""
echo "ℹ️  Wake word models will be downloaded automatically on first run"
echo "   by the openwakeword library."

echo ""
echo "✓ Model setup complete!"
echo ""
echo "Models directory: $MODELS_DIR"
echo "  - en_US-lessac-medium.onnx (Piper TTS voice)"
echo ""
echo "Next steps:"
echo "  1. Copy config/settings.json.example to config/settings.json"
echo "  2. Edit config/settings.json with your Telegram credentials"
echo "  3. Run: python src/voice_assistant_gui.py"
