# Lighthouse.ai

> Voice-driven web navigator for blind and low-vision users

Lighthouse.ai is a voice-controlled assistant that lets blind and low-vision users browse and operate websites hands-free. Users speak commands; the agent controls the browser and announces what's on screen after every action—reliably and safely.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+ (recommended) or Python 3.9+
- Chrome/Chromium browser
- macOS, Linux, or Windows
- For macOS: Xcode Command Line Tools (`xcode-select --install`)

### Installation

```bash
# Clone the repository
git clone https://github.com/lighthouse-ai/lighthouse.git
cd lighthouse

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install system dependencies (macOS)
brew install portaudio  # Required for PyAudio

# Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Copy environment configuration
cp env.example .env
```

### Running Lighthouse.ai

#### CLI Mode (Voice Interface)
```bash
# Activate virtual environment
source venv/bin/activate

# Run CLI with voice commands
python cli.py
```

#### API Mode (Testing/Development)
```bash
# Activate virtual environment
source venv/bin/activate

# Run API server
python main.py
# or with custom port
API_PORT=8001 python main.py
```

Visit `http://localhost:8000/docs` (or your custom port) for interactive API documentation.

## 🔧 Troubleshooting

### Common Issues

**TTS Engine Not Working (macOS)**
- Install PyObjC: `pip install PyObjC>=9.0.0`
- The app will continue to work without voice feedback

**Port Already in Use**
- Kill existing process: `lsof -ti:8000 | xargs kill -9`
- Use different port: `API_PORT=8001 python main.py`

**Chrome Driver Issues**
- The app automatically handles Chrome driver setup
- If issues persist, manually install Chrome/Chromium browser

## 🎯 Core Features

### Voice Commands
- **Navigate**: "Go to google.com"
- **Click**: "Click the search button"
- **Type**: "Type hello world"
- **Submit**: "Submit the form"
- **Describe**: "Describe this page"
- **List**: "List all buttons"
- **Stop**: "Stop" or "Cancel"

### Safety Features
- **Domain Allowlist**: Only navigate to approved domains
- **Confirmation Gates**: Destructive actions require confirmation
- **Local Processing**: All speech processing happens locally by default

### Accessibility
- **Screen Descriptions**: Clear, concise page summaries
- **Element Disambiguation**: Numbered lists when multiple matches
- **Change Detection**: Reports what changed after each action

## 🔧 Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

```bash
# Domain allowlist (comma-separated)
ALLOWED_DOMAINS=google.com,amazon.com,github.com,wikipedia.org

# Browser settings
HEADLESS_MODE=false
BROWSER_TIMEOUT=10

# Audio settings
AUDIO_DEVICE=default
VAD_AGGRESSIVENESS=2

# Privacy settings
LOCAL_PROCESSING=true
LOG_LEVEL=INFO
```

### Domain Allowlist
Edit `config/domains.yaml` to manage allowed domains:

```yaml
allowed_domains:
  - google.com
  - amazon.com
  - github.com
  - wikipedia.org
  - example.com

restricted_actions:
  - delete
  - purchase
  - payment
  - account_change
```

## 🛡️ Privacy & Security

### Privacy-First Design
- **Local Processing**: Speech recognition and synthesis happen on your device
- **No Audio Storage**: Audio is processed in real-time and discarded
- **Redacted Logs**: Sensitive information is automatically redacted
- **Opt-in Cloud**: Cloud services only used with explicit consent

### Security Features
- **Domain Restrictions**: Only navigate to approved websites
- **Action Confirmation**: Destructive actions require verbal confirmation
- **Sandboxed Browser**: Isolated browser profile for safety
- **Audit Trail**: All actions are logged for review

### Data Handling
- **No Personal Data**: We don't collect or store personal information
- **Local Storage**: All data stays on your device
- **Encrypted Logs**: Session logs are encrypted locally
- **Transparent Processing**: Open source code for full transparency

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/test_cli.py -v
pytest tests/test_api.py -v
pytest tests/test_browser.py -v

# Test on target sites
make test-sites

# Check code quality
make lint
make format
```

## 📁 Project Structure

```
lighthouse/
├── cli.py                 # CLI entry point
├── main.py                # FastAPI service
├── config/                # Configuration files
├── core/                  # Core functionality
│   ├── asr.py            # Speech recognition
│   ├── nlu.py            # Natural language understanding
│   ├── tts.py            # Text-to-speech
│   ├── browser.py        # Browser automation
│   ├── safety.py         # Safety controls
│   └── state.py          # Session management
├── api/                   # REST API
├── utils/                 # Utilities
└── tests/                 # Test suite
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run tests: `make test`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
make dev-install

# Setup pre-commit hooks
pre-commit install

# Run development server
make dev
```

## 📋 Roadmap

### v1.0 (Current MVP)
- [x] Basic voice commands
- [x] Browser automation
- [x] Screen descriptions
- [x] Safety controls
- [x] Local processing

### v1.1 (Planned)
- [ ] Hotword detection
- [ ] Advanced form handling
- [ ] Table navigation
- [ ] Multi-step workflows

### v2.0 (Future)
- [ ] Cloud TTS integration
- [ ] Advanced error recovery
- [ ] Custom command training
- [ ] Mobile app

## 🆘 Troubleshooting

### Common Issues

**"Chrome not found"**
```bash
make install-chrome
make check-chrome
```

**"Audio device not working"**
```bash
# Check available audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"
```

**"Whisper model not found"**
```bash
make download-models
```

**"Permission denied"**
```bash
# On macOS, grant microphone permissions in System Preferences
# On Linux, add user to audio group
sudo usermod -a -G audio $USER
```

### Getting Help

- 📖 [Documentation](https://lighthouse-ai.readthedocs.io)
- 🐛 [Report Issues](https://github.com/lighthouse-ai/lighthouse/issues)
- 💬 [Discussions](https://github.com/lighthouse-ai/lighthouse/discussions)
- 📧 [Email Support](mailto:support@lighthouse.ai)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Coqui TTS](https://github.com/coqui-ai/TTS) for text-to-speech
- [Selenium](https://selenium.dev/) for browser automation
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

---

**Made with ❤️ for the accessibility community**
