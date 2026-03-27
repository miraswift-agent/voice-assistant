# Voice Assistant for OpenClaw

Real-time voice control for AI agents with streaming responses and visual feedback.

## Features

- **Wake word detection** (openwakeword: Alexa, Hey Jarvis, Hey Mycroft, Hey Rhasspy)
- **Voice activity detection** (webrtcvad)
- **Speech-to-text** (faster-whisper with tiny int8 model)
- **Text-to-speech** (Piper TTS with en_US-lessac-medium.onnx)
- **Streaming responses** via webhook callbacks (real-time chunk delivery)
- **Visual feedback** with animated blue orb display
- **Device management** (easy Bluetooth/USB audio switching)

## Architecture

```
┌─────────────┐                    ┌──────────────┐
│ Raspberry Pi│                    │   OpenClaw   │
│ 1. Wake word│◄───────────────────│   (Mira)     │
│ 2. Record   │   POST /response   │              │
│ 3. Whisper  │   {sentence chunks}│              │
│ 4. HTTP POST├──────────────────► │ 5. Detect    │
│    + callback│   🎤 Voice + URL   │    callback  │
│    URL       │                    │ 6. Stream    │
│ 7. Webhook   │                    │    response  │
│    receives  │                    │    chunks    │
│ 8. Speak     │                    │              │
│    each chunk│                    │              │
│ 9. Orb viz   │                    │              │
└─────────────┘                    └──────────────┘
```

## Hardware Requirements

- Raspberry Pi (tested on Pi 4/5)
- USB microphone or Bluetooth headset
- USB speakers, 3.5mm audio out, or Bluetooth audio
- Optional: Display for visual orb interface

## Installation

```bash
# Clone repository
git clone https://github.com/miraswift-agent/voice-assistant.git
cd voice-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download Piper TTS model
bash scripts/download-models.sh
```

## Configuration

Edit `config/settings.json`:

```json
{
  "wake_words": ["alexa", "hey jarvis"],
  "audio_input": "default",
  "audio_output": "default",
  "whisper_model": "tiny.en",
  "piper_model": "models/en_US-lessac-medium.onnx",
  "webhook_port": 8765,
  "telegram_token": "<your-bot-token>",
  "openclaw_chat_id": "<mira-chat-id>"
}
```

## Usage

### Command Line (headless)

```bash
source venv/bin/activate
python src/voice_assistant.py
```

### GUI Mode (with visual orb)

```bash
source venv/bin/activate
python src/voice_assistant_gui.py
```

Or use desktop launcher: `~/Desktop/voice-assistant.desktop`

## Project Structure

```
voice-assistant/
├── README.md
├── requirements.txt
├── config/
│   └── settings.json          # User configuration
├── src/
│   ├── voice_assistant.py     # Main voice loop (CLI)
│   ├── voice_assistant_gui.py # GUI with orb visualization
│   ├── wake_word_detector.py  # Wake word detection
│   ├── transcriber.py         # Whisper transcription
│   ├── tts_engine.py          # Piper TTS wrapper
│   ├── webhook_server.py      # Callback receiver
│   └── orb_visualizer.py      # Blue orb animation
├── models/
│   └── en_US-lessac-medium.onnx  # Piper voice model
└── scripts/
    └── download-models.sh     # Model download helper
```

## GUI Features

### Blue Orb States

- **Idle:** Gentle breathing pulse
- **Listening:** Faster pulse + waveform from mic
- **Processing:** Spinner animation
- **Speaking:** Waveform synced to TTS output

### Settings Panel

- Audio input device selection (USB/Bluetooth/default)
- Audio output device selection (USB/Bluetooth/3.5mm)
- Wake word configuration
- Volume controls (input/output)
- Test audio functionality

## Development

Built by [Mira Swift](https://github.com/miraswift-agent) (AI agent) in collaboration with Tom Swift.

**Timeline:**
- March 20, 2026: Initial CLI version with streaming webhook callbacks
- March 27, 2026: GUI with visual orb feedback and device management

## License

MIT
