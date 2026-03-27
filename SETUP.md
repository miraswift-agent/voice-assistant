# Setup Guide for Raspberry Pi

## Prerequisites

- Raspberry Pi (4 or 5 recommended)
- Raspberry Pi OS (Desktop or Lite with GUI)
- USB microphone or Bluetooth headset
- Speakers (USB, 3.5mm, or Bluetooth)
- Internet connection

## Installation

### 1. Clone Repository

```bash
cd ~
git clone https://github.com/miraswift-agent/voice-assistant.git
cd voice-assistant
```

### 2. Install System Dependencies

```bash
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    python3-pyaudio \
    libsndfile1 \
    wget \
    espeak-ng
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Download Models

```bash
bash scripts/download-models.sh
```

This downloads the Piper TTS voice model (~60MB). Wake word models download automatically on first run.

### 6. Configure Settings

```bash
cp config/settings.json.example config/settings.json
nano config/settings.json
```

**Required settings:**
- `telegram_token`: Your Telegram bot token (get from @BotFather)
- `openclaw_chat_id`: Mira's Telegram chat ID

**Optional settings:**
- `wake_words`: Which wake words to enable
- `audio_input_device`: Specific device name or "default"
- `audio_output_device`: Specific device name or "default"
- `volume_input`: Input gain (0.0 to 2.0)
- `volume_output`: Output volume (0.0 to 2.0)

### 7. Test Audio Devices

```bash
# List available devices
python -c "import pyaudio; p=pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]; p.terminate()"

# Test microphone (record 3 seconds)
arecord -d 3 test.wav && aplay test.wav
```

## Running

### CLI Mode (Headless)

```bash
source venv/bin/activate
python src/voice_assistant.py
```

**Output:**
```
====================================================================
Voice Assistant Started
Wake words: alexa, hey jarvis
Webhook: http://0.0.0.0:8765/response
====================================================================

[Listening] Waiting for wake word...
```

### GUI Mode (with Visual Orb)

```bash
source venv/bin/activate
python src/voice_assistant_gui.py
```

**Features:**
- Animated blue orb with 4 states
- Settings dialog for device switching
- Volume controls
- Wake word configuration

### Desktop Launcher (Recommended)

```bash
# Copy launcher to desktop
cp scripts/voice-assistant.desktop ~/Desktop/
chmod +x ~/Desktop/voice-assistant.desktop

# Update paths in launcher if needed
nano ~/Desktop/voice-assistant.desktop
```

Double-click "Voice Assistant" icon on desktop to start!

## Usage

1. **Start the assistant** (CLI or GUI)
2. **Wait for "Listening..."** message
3. **Say wake word:** "Alexa" or "Hey Jarvis" (configured in settings)
4. **Speak your question** when you hear the prompt
5. **Wait for response** - Mira will stream back sentences and speak them

## Troubleshooting

### No Wake Word Detection

- Check microphone is working: `arecord -d 3 test.wav && aplay test.wav`
- Verify device in settings: `audio_input_device`
- Try increasing `volume_input` in settings

### No Audio Output

- Check speaker is working: `speaker-test -t wav`
- Verify device in settings: `audio_output_device`
- Try different output device in GUI settings

### Telegram Not Working

- Verify bot token is correct
- Check chat ID is Mira's Telegram user ID
- Test bot manually: `https://api.telegram.org/bot<TOKEN>/getMe`

### VAD Too Sensitive/Not Sensitive

- Adjust `vad_aggressiveness` (1-3, higher = more aggressive)
- Adjust `silence_duration_ms` (how long to wait before stopping recording)

### Models Not Downloaded

```bash
cd ~/voice-assistant
bash scripts/download-models.sh
```

### Permission Denied on Audio

```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Reboot for changes to take effect
sudo reboot
```

## Network Configuration

The webhook server runs on port 8765 by default. If Mira is on a different machine:

1. Ensure Pi is reachable from Mira's machine
2. Update callback URL in code if needed (hostname resolution)
3. Or use Tailscale/VPN for reliable connectivity

## Auto-start on Boot (Optional)

### Systemd Service

Create `/etc/systemd/system/voice-assistant.service`:

```ini
[Unit]
Description=Voice Assistant
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/voice-assistant
ExecStart=/home/pi/voice-assistant/venv/bin/python /home/pi/voice-assistant/src/voice_assistant_gui.py
Restart=always
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=graphical.target
```

Enable:
```bash
sudo systemctl enable voice-assistant
sudo systemctl start voice-assistant
```

## Updating

```bash
cd ~/voice-assistant
git pull origin master
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

## Support

Issues: https://github.com/miraswift-agent/voice-assistant/issues
