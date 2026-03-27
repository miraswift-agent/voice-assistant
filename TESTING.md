# Testing the GUI

## Quick Start (On Raspberry Pi)

### 1. Pull Latest Code

```bash
cd ~/voice-assistant
git pull origin master
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 3. Make Sure Voice Server is Running on mirapc

SSH into mirapc or check if it's already running:

```bash
# On mirapc
cd ~/voice-assistant/mirapc
python voice_server.py
```

You should see:
```
🎤 Voice server starting on port 8765...
   Model: qwen2.5:14b-instruct
   Endpoint: http://citadel:11434/v1/chat/completions
```

### 4. Launch the GUI on Pi

```bash
python src/voice_assistant_gui.py
```

**What you should see:**
- Black window with blue orb in center
- "Ready to start" status text
- Green "▶ Start Listening" button

## Testing Steps

### Step 1: Start the Assistant

1. Click the **▶ Start Listening** button
2. Status should change to "Loading models..."
3. After ~5 seconds: "Listening for wake word..."
4. Blue orb should pulse gently (idle state)

### Step 2: Trigger Wake Word

1. Say **"Alexa"** or **"Hey Jarvis"** clearly
2. **Watch the orb:**
   - Should pulse faster
   - Waveform rings appear around orb (visualizing your audio)
3. **Status text:** "Wake word detected! Speak now..."

### Step 3: Ask a Question

1. Speak your question (e.g., "What time is it?")
2. **Watch the orb:**
   - Continues showing waveform while you speak
   - Automatically stops after 1.5 seconds of silence
3. **Status text:** "Transcribing..." → "You: [your question]"
4. **Orb changes:** Spinner animation (processing state)

### Step 4: Hear Response

1. **Status text:** "Asking Mira..." → "Mira: [response]"
2. **Orb changes:** Waveform bars around orb (speaking state)
3. **Audio:** You should hear Piper TTS speaking the response
4. **After response:** Returns to idle (gentle pulse)

### Step 5: Multiple Conversations

- Orb should return to idle state
- Say wake word again to ask another question
- Repeat as many times as you want

### Step 6: Stop

1. Click **⏸ Stop Listening** button (now red)
2. Orb stays in idle animation
3. Status: "Stopped"

## What to Look For

### ✅ Working States:

1. **Idle (Blue pulse):** Gentle breathing animation
2. **Listening (Active pulse + rings):** Faster pulse with waveform rings from microphone
3. **Processing (Spinner):** Rotating dots around orb
4. **Speaking (Waveform bars):** Bars radiating from orb synced to speech

### ✅ Expected Flow:

```
Idle → [Wake word] → Listening → Processing → Speaking → Idle
```

### ❌ Common Issues:

**Wake word not detected:**
- Check microphone is working: `arecord -d 3 test.wav && aplay test.wav`
- Speak louder and clearer
- Try different wake word ("Hey Jarvis" might work better than "Alexa")

**No audio output:**
- Check speakers: `speaker-test -t wav`
- Verify audio device is selected correctly
- Check volume (both system and application)

**"Error: couldn't reach voice server":**
- Ping mirapc: `ping mirapc`
- Check voice server is running: `curl http://mirapc:8765/health`
- Verify network connectivity

**Orb animations laggy:**
- Normal on older Pi models
- Animations are cosmetic, voice functionality unaffected

## Advanced Testing

### Test Different Wake Words

Edit code to try all wake words:
- "Alexa"
- "Hey Jarvis"
- "Hey Mycroft"
- "Hey Rhasspy"

### Test Audio Visualization

1. Start assistant
2. Trigger wake word
3. **Speak loudly:** Watch waveform rings grow
4. **Speak softly:** Rings should be smaller
5. **Silence:** Rings should disappear

### Test Long Questions

- Try speaking for 5-10 seconds
- Should auto-stop after 1.5s of silence
- Max recording: 12 seconds

### Test Streaming Responses

- Ask: "Tell me about the solar system"
- Watch status text update with each sentence
- Orb should show waveform for each spoken chunk
- Responses should come in real-time (not all at once)

## Debugging

### Enable Verbose Output

Edit `voice_assistant_gui.py` and add at the top:

```python
DEBUG = True
```

Then check terminal output while running.

### Check Logs

```bash
# On mirapc, watch voice server logs
tail -f ~/voice-assistant/mirapc/voice_server.log
```

### Network Test

```bash
# On Pi, test server manually
curl -X POST http://mirapc:8765/voice/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

Should stream back JSON chunks.

## Success Criteria

✅ GUI launches without errors  
✅ Blue orb animates smoothly  
✅ Wake word triggers listening state  
✅ Audio waveform appears during speech  
✅ Transcription works correctly  
✅ Response streams from Mira  
✅ TTS speaks each chunk  
✅ Orb returns to idle after response  
✅ Can ask multiple questions in a row  
✅ Clean shutdown when stopped  

## Report Issues

If something doesn't work:
1. Note which step failed
2. Check terminal output for errors
3. Take screenshot of GUI state
4. Report on GitHub: https://github.com/miraswift-agent/voice-assistant/issues

## Next Steps After Testing

Once basic functionality works:
- Test device switching in settings (future feature)
- Test wake word selection (future feature)
- Test volume controls (future feature)
- Desktop launcher integration
- Auto-start on boot setup
