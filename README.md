# Flow: Zero-Latency Dictation Daemon

A highly optimized, system-wide push-to-talk dictation daemon for Arch Linux and Xorg. 

Flow acts as an open-source clone of "Wispr Flow," designed strictly for speed and minimalism. It keeps a local AI transcription model warm in memory and captures audio directly to RAM, entirely bypassing the disk to achieve sub-second "time-to-text" injection into any active X11 window.

## ⚡ Core Architecture & Optimizations

* **Zero Disk I/O:** Audio is captured directly into a `numpy` `float32` memory buffer using `sounddevice`. No temporary `.wav` files are ever written to your drive.
* **VRAM/RAM Resident:** Uses `faster-whisper` (CTranslate2) loaded at boot. The model stays warm in the background, eliminating initialization latency on keypress.
* **INT8 Quantization:** Forced 8-bit quantization massively reduces CPU overhead and drops RAM usage from ~2GB down to ~600MB without sacrificing accuracy.
* **VAD Silence Trimming:** Implements WebRTC Voice Activity Detection to instantly strip trailing and leading silence before inference, drastically speeding up processing time.
* **Raw Keystroke Injection:** Uses `xdotool` to simulate rapid keystrokes (`--delay 0`), bypassing the system clipboard entirely and working universally across native terminals (Alacritty, st) and GUI browsers.

## 📦 Prerequisites

This daemon is built for Arch Linux running an X11 session. You will need system audio headers and Xorg automation tools.

```bash
sudo pacman -S portaudio xdotool xclip pulseaudio-alsa libpulse

🚀 Installation
1. Clone the repository

Bash
mkdir -p ~/.local/share/wispr-clone
cd ~/.local/share/wispr-clone
git clone <your-repo-url> .
2. Set up the Python Environment
Because this relies on heavy system C-extensions (like numpy and sounddevice), it is highly recommended to use the system site-packages for the base libraries and only use pip for the AI engine.

Bash
sudo pacman -S python-numpy python-sounddevice python-pynput python-pip
python -m venv venv --system-site-packages
source venv/bin/activate
pip install faster-whisper==1.0.1
3. Install the Systemd User Service
Create a systemd user service to ensure the daemon boots silently in the background on login.

Bash
mkdir -p ~/.config/systemd/user
cp wispr-clone.service ~/.config/systemd/user/
Enable and start the daemon:

Bash
systemctl --user daemon-reload
systemctl --user enable --now wispr-clone.service
🎙️ Usage
Once the service is running, it operates completely invisibly in the background.

Click into any application (Terminal, Browser, Editor).

Press and hold Super + Shift.

You will hear a brief startup chime. Speak your sentence.

Release the keys.

You will hear a stop chime, and your text will be instantly typed into the active window.

⚙️ Configuration
You can easily tweak the daemon by editing the variables at the top of flow.py:

HOTKEY_MODIFIERS: Change the trigger keys (default is {'cmd', 'shift'}). Note: pynput refers to the Super/Windows key as cmd.

MODEL_SIZE: Default is "small.en". If you are on very constrained hardware, drop this to "base.en" for ~70x real-time speed.

HALLUCINATIONS: A customizable set of phrases to drop. Background noise can occasionally cause Whisper to hallucinate phrases like "Thanks for watching." The script catches and silently drops these.

🔍 Debugging
If the hotkeys are unresponsive or text isn't injecting, check the live systemd logs:

Bash
journalctl --user -u wispr-clone.service -f
Note: The first time you run the daemon, it will pause for a minute or two to download the Whisper weights from the Hugging Face hub. Subsequent boots will load instantly from your local ~/.cache/huggingface/hub/ directory
