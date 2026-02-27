# Jarvis AI Assistant

A Python-based AI assistant that listens, automates tasks, and answers queries using AI. Jarvis is a voice-activated virtual assistant powered by Google Gemini AI, capable of executing various system commands, web automation, and real-time interactions.

## ✨ Features

### 🎤 Voice & Audio
- **Hotword Detection**: Continuous listening for "Jarvis" wake word using PorcupineNLP
- **Voice Commands**: Natural language voice input via speech recognition
- **Text-to-Speech**: AI responses delivered via system text-to-speech engine
- **Real-time Audio Processing**: Multiprocessing-based architecture for seamless hotword detection

### 🧠 AI Intelligence
- **Google Gemini Integration**: Advanced AI responses powered by Google's Gemini 1.5 Flash model
- **Intelligent Fallback**: Local responses when AI quota limits are reached
- **Context-Aware Commands**: Smart command interpretation and execution

### 🚀 Application Control
- **App Launcher**: Open applications by voice command (Chrome, Notepad, Calculator, etc.)
- **System Control**: Adjust volume, brightness, sleep mode
- **Window Management**: Automate application interactions

### 🌐 Web Automation
- **YouTube Integration**: Search and play YouTube videos by voice
- **Google Search**: Perform web searches automatically
- **Browser Automation**: Open websites and execute web-based tasks

### 📱 Communication
- **WhatsApp Integration**: Send WhatsApp messages and make calls by voice
- **Contact Management**: Store and manage WhatsApp contacts in SQLite database
- **Smart Contact Lookup**: Find and interact with saved contacts

### 💾 System Features
- **System Information**: Get CPU, RAM, battery, and network status
- **File Operations**: Type and interact with system through voice
- **Camera Access**: Webcam integration for video capture
- **Morning Briefing**: Automated daily briefing with news and weather
- **Database Management**: SQLite for contact and user data persistence

### 🎨 User Interface
- **Web-Based UI**: Interactive Eel-based web interface
- **Real-time Display**: Visual feedback with SiriWave animations
- **Message Logging**: Track command history and responses

## 🎥 Demo
Watch the project demo here:  
[▶ Click to watch on Google Drive](https://drive.google.com/file/d/1XyBkBBKozAUZl2eCrrluOpvJMlcCnBbG/view?usp=drive_link)

https://drive.google.com/file/d/1Fh1WCBQKs93mI5DrMug-RSVilPidpMU8/view?usp=drive_link

https://drive.google.com/file/d/12CK7oOCxwfpRuulzTwjDSVQE6_2vvf6U/view?usp=drive_link

https://drive.google.com/file/d/1r3gOhni1Pygp8y3SWbX2h1KZi0yegg_u/view?usp=drive_link

## 🏗️ Architecture

Jarvis uses a **multiprocessing architecture** for optimal performance:
- **Process 1**: Main application + Eel web server (handles commands and UI)
- **Process 2**: Hotword detection daemon (continuous listening without blocking main thread)
- **Auto-Restart**: Supervisor loop automatically restarts failed processes

## ⚙️ Installation

### Prerequisites
- Python 3.11+
- Microphone for voice input
- Internet connection for AI responses and web features
- Google Generative AI API key

### Setup Steps

```bash
git clone https://github.com/yourusername/Jarvis.git
cd Jarvis
python -m venv envjarvis

# Windows
envjarvis\Scripts\activate

# Mac/Linux
source envjarvis/bin/activate

pip install -r requirement.txt
```

## 🔑 Configuration

1. **API Keys**: Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_google_generative_ai_key
   ```

2. **Database Initialization** (First time setup):
   ```bash
   python init_db.py
   ```

3. **Check Available Models**:
   ```bash
   python list_models.py
   ```

## 🚀 Running Jarvis

### Main Mode (Recommended)
```bash
python run.py
```
This starts both the main application and hotword detection with automatic restart capabilities.

### Direct Mode
```bash
python main.py
```
To run just the main application without multiprocessing.

## 📊 Project Structure

- **engine/**: Core functionality modules
  - `command.py`: Speech recognition, TTS, and Gemini AI integration
  - `features.py`: Feature implementations (apps, web automation, WhatsApp, etc.)
  - `config.py`: Configuration settings
  - `helper.py`: Utility functions
- **www/**: Web UI files (HTML, CSS, JavaScript)
- **envjarvis/**: Virtual environment
- **jarvis.db**: SQLite database for contacts and data

## 📦 Dependencies

Key packages:
- `google-generativeai`: Gemini API integration
- `pyttsx3`: Text-to-speech
- `SpeechRecognition`: Voice input
- `pvporcupine`: Hotword detection
- `pywhatkit`: WhatsApp automation
- `eel`: Web-based UI
- `bottle`: Web server
- `pyaudio`: Audio input/output
- `psutil`: System information

See `requirement.txt` for complete dependency list.

## 🔧 Troubleshooting

- **Hotword Not Detected**: Check microphone settings and PorcupineNLP model validity
- **Port Already in Use**: The application automatically kills processes on port 8000
- **API Quota Exceeded**: Jarvis will use local fallback responses until quota resets
- **Database Lockups**: Use `init_db.py` to reinitialize the database

## 📝 Logging

Diagnostic logs are available in:
- `diag_log.txt`: General diagnostics
- `models_log.txt`: Model and API information

## 📄 License

[Add your license information here]
