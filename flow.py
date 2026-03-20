#!/usr/bin/env python3
import os
import subprocess
import numpy as np
import sounddevice as sd
from pynput import keyboard
from faster_whisper import WhisperModel

# ==========================================
# CONFIGURATION
# ==========================================
HOTKEY_MODIFIERS = {'cmd', 'shift', 'alt'}  # 'cmd' is the Super/Windows key in pynput
SAMPLE_RATE = 16000
CHANNELS = 1
MODEL_SIZE = "small.en"  # Drop to "base.en" if you need even faster inference

HALLUCINATIONS = {
    "Thank you.", "Thanks for watching.", "Thanks for watching!", 
    "Subscribe to the channel.", "Please subscribe.", "Amara.org",
    "Bye.", "You"
}

# Standard Arch/Freedesktop UI sounds
SOUND_START = "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga"
SOUND_STOP = "/usr/share/sounds/freedesktop/stereo/message.oga"


# ==========================================
# AUDIO CAPTURE (Zero-IO Memory Stream)
# ==========================================
class AudioCapture:
    def __init__(self):
        self.stream = None
        self.audio_buffer = []
        self.is_recording = False

    def play_sound(self, sound_path):
        """Non-blocking audio feedback using paplay."""
        if os.path.exists(sound_path):
            subprocess.Popen(['paplay', sound_path], stderr=subprocess.DEVNULL)

    def _callback(self, indata, frames, time, status):
        if self.is_recording:
            self.audio_buffer.append(indata.copy())

    def start(self):
        self.audio_buffer = []
        self.is_recording = True
        self.play_sound(SOUND_START)
        
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            callback=self._callback
        )
        self.stream.start()

    def stop(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        self.play_sound(SOUND_STOP)

        if not self.audio_buffer:
            return None

        # Flatten the buffer list into a single 1D numpy array
        return np.concatenate(self.audio_buffer, axis=0).flatten()


# ==========================================
# TRANSCRIPTION ENGINE (VRAM Resident)
# ==========================================
class TranscriptionEngine:
    def __init__(self):
        # Let faster-whisper natively auto-detect your hardware
        self.device = "auto"
        self.compute_type = "int8" 
        
        print(f"Loading {MODEL_SIZE} on {self.device} ({self.compute_type})...")
        self.model = WhisperModel(
            MODEL_SIZE, 
            device=self.device, 
            compute_type=self.compute_type
        )
        print("Model loaded and warm. Ready for dictation.")

    def transcribe(self, audio_data):
        if audio_data is None or len(audio_data) < SAMPLE_RATE * 0.4:
            return "" # Ignore tiny audio blips

        # VAD filter massively speeds up processing by stripping silence
        segments, _ = self.model.transcribe(
            audio_data, 
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400)
        )

        text = "".join(segment.text for segment in segments).strip()

        if text in HALLUCINATIONS or text.strip() == "":
            return ""
            
        return text


# ==========================================
# SYSTEM DAEMON & X11 INJECTION
# ==========================================
class DictationDaemon:
    def __init__(self):
        self.audio = AudioCapture()
        self.engine = TranscriptionEngine()
        self.current_keys = set()
        self.is_recording = False

    def inject_text(self, text):
        """Injects text into the active Xorg window by simulating rapid keystrokes."""
        if not text:
            return
            
        print(f"Typing: {text}")
        
        # --clearmodifiers: Ensures your physical Super/Shift keys don't hijack the typing
        # --delay 0: Forces xdotool to type as fast as the X server can physically accept it
        subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '0', text])
        
    def on_press(self, key):
        try:
            key_name = key.name if hasattr(key, 'name') else key.char
            if key_name in HOTKEY_MODIFIERS:
                self.current_keys.add(key_name)
                
                if HOTKEY_MODIFIERS.issubset(self.current_keys) and not self.is_recording:
                    print("Recording...")
                    self.is_recording = True
                    self.audio.start()
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            key_name = key.name if hasattr(key, 'name') else key.char
            if key_name in HOTKEY_MODIFIERS:
                if key_name in self.current_keys:
                    self.current_keys.remove(key_name)
                
                if self.is_recording:
                    self.is_recording = False
                    print("Processing...")
                    audio_data = self.audio.stop()
                    
                    text = self.engine.transcribe(audio_data)
                    if text:
                        # Append a leading space so sentences flow naturally when typing
                        self.inject_text(" " + text)
        except AttributeError:
            pass

    def run(self):
        print(f"Daemon listening for {HOTKEY_MODIFIERS}...")
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

if __name__ == "__main__":
    daemon = DictationDaemon()
    daemon.run()
