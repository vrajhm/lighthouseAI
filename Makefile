# Lighthouse.ai MVP Makefile

.PHONY: help install dev-install test lint format clean run-cli run-api setup test-sites

help: ## Show this help message
	@echo "Lighthouse.ai MVP - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

dev-install: ## Install development dependencies
	pip install -e ".[dev]"

setup: ## Initial setup - install deps and download models
	@echo "Setting up Lighthouse.ai..."
	pip install -e ".[dev]"
	@echo "Downloading Whisper models..."
	python -c "import whisper; whisper.load_model('base')"
	@echo "Downloading Coqui TTS models..."
	python -c "from TTS.api import TTS; TTS.list_models()"
	@echo "Setup complete! Run 'make run-cli' to start."

test: ## Run tests
	pytest tests/ -v --cov=lighthouse --cov-report=html

lint: ## Run linting
	black --check lighthouse/ tests/
	flake8 lighthouse/ tests/
	mypy lighthouse/

format: ## Format code
	black lighthouse/ tests/
	isort lighthouse/ tests/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

run-cli: ## Run CLI interface
	python cli.py

run-api: ## Run FastAPI service
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test-sites: ## Test on target sites
	python scripts/test_sites.py

check-deps: ## Check if all dependencies are available
	@echo "Checking dependencies..."
	@python -c "import selenium; print('✓ Selenium')" || echo "✗ Selenium missing"
	@python -c "import faster_whisper; print('✓ faster-whisper')" || echo "✗ faster-whisper missing"
	@python -c "import TTS; print('✓ Coqui TTS')" || echo "✗ Coqui TTS missing"
	@python -c "import webrtcvad; print('✓ WebRTC VAD')" || echo "✗ WebRTC VAD missing"
	@python -c "import fastapi; print('✓ FastAPI')" || echo "✗ FastAPI missing"
	@python -c "import pydantic; print('✓ Pydantic')" || echo "✗ Pydantic missing"

download-models: ## Download required ML models
	@echo "Downloading Whisper base model..."
	python -c "import whisper; whisper.load_model('base')"
	@echo "Downloading Coqui TTS models..."
	python -c "from TTS.api import TTS; TTS.list_models()"

build: ## Build package
	python -m build

install-chrome: ## Install Chrome/Chromium (macOS)
	@echo "Installing Chrome via Homebrew..."
	brew install --cask google-chrome
	@echo "Chrome installed. Make sure ChromeDriver is available in PATH."

check-chrome: ## Check Chrome installation
	@echo "Checking Chrome installation..."
	@which google-chrome || echo "Chrome not found in PATH"
	@which chromedriver || echo "ChromeDriver not found in PATH"

dev: ## Start development environment
	@echo "Starting development environment..."
	@echo "API will be available at http://localhost:8000"
	@echo "API docs at http://localhost:8000/docs"
	@echo "Press Ctrl+C to stop"
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Environment setup
.env:
	@echo "Creating .env file from template..."
	cp env.example .env
	@echo "Please edit .env with your configuration"

# Quick start for new developers
quickstart: .env dev-install download-models check-chrome ## Quick setup for new developers
	@echo "Quickstart complete!"
	@echo "Run 'make run-cli' to start the CLI or 'make run-api' for the web service"
