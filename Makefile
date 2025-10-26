# LIhouses Makefile
# Convenient commands for managing the web interface and running scripts

.PHONY: help web start stop install clean

# Default target - show help
help:
	@echo "LIhouses - Available Commands"
	@echo "=============================="
	@echo ""
	@echo "Web Interface:"
	@echo "  make web      - Start the web interface (opens browser automatically)"
	@echo "  make start    - Alias for 'make web'"
	@echo "  make stop     - Stop the web server (Ctrl+C in terminal)"
	@echo ""
	@echo "Development:"
	@echo "  make install  - Install Python dependencies"
	@echo "  make clean    - Remove temporary files and outputs"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. Copy .env.example to .env and add your API keys"
	@echo "  2. Run 'make install' to install dependencies"
	@echo "  3. Run 'make web' to start the web interface"
	@echo ""

# Start the web interface
web:
	@echo "Starting LIhouses Web Interface..."
	@echo "Press Ctrl+C to stop the server"
	@echo ""
	pipenv run python src/web/app.py

# Alias for web
start: web

# Stop instruction (Ctrl+C stops the running server)
stop:
	@echo "To stop the server:"
	@echo "  - Press Ctrl+C in the terminal where the server is running"
	@echo ""
	@echo "If running in background, find the process:"
	@echo "  ps aux | grep 'src/web/app.py'"
	@echo "  kill <process_id>"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pipenv install
	@echo ""
	@echo "✓ Dependencies installed"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Copy .env.example to .env"
	@echo "  2. Add your API keys to .env"
	@echo "  3. Run 'make web' to start the interface"

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	rm -rf .tmp/*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleanup complete"
