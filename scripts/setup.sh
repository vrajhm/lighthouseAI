#!/bin/bash
# Setup script for Lighthouse.ai

set -e

echo "🚀 Setting up Lighthouse.ai..."

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9+ is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected. Consider using one:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev]"

# Download models
echo "Downloading ML models..."
echo "  - Whisper model..."
python -c "import whisper; whisper.load_model('base')" || echo "⚠️  Whisper model download failed"

echo "  - Coqui TTS models..."
python -c "from TTS.api import TTS; TTS.list_models()" || echo "⚠️  TTS model download failed"

# Check Chrome installation
echo "Checking Chrome installation..."
if command -v google-chrome &> /dev/null; then
    echo "✅ Chrome found"
elif command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium found"
else
    echo "⚠️  Chrome/Chromium not found. Please install:"
    echo "   macOS: brew install --cask google-chrome"
    echo "   Ubuntu: sudo apt-get install google-chrome-stable"
    echo "   Or download from: https://www.google.com/chrome/"
fi

# Check ChromeDriver
echo "Checking ChromeDriver..."
if command -v chromedriver &> /dev/null; then
    echo "✅ ChromeDriver found"
else
    echo "⚠️  ChromeDriver not found. It will be downloaded automatically by undetected-chromedriver"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
else
    echo "✅ .env file already exists"
fi

# Run basic tests
echo "Running basic tests..."
python -m pytest lighthouse/tests/test_basic.py -v || echo "⚠️  Some tests failed"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run 'make run-cli' to start the CLI interface"
echo "3. Run 'make run-api' to start the web API"
echo "4. Run 'make test-sites' to test on target websites"
echo ""
echo "For help, run 'make help'"
