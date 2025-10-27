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
	@echo "  make stop     - Stop the web server"
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

# Stop the web server
stop:
	@echo "Stopping LIhouses Web Interface..."
	@PID=$$(netstat -ano | grep :8080 | grep LISTENING | awk '{print $$5}' | head -1); \
	if [ -n "$$PID" ]; then \
		echo "Found Flask server on port 8080 (PID: $$PID)"; \
		taskkill //PID $$PID //F; \
		echo "[OK] Server stopped"; \
	else \
		echo "No server running on port 8080"; \
	fi

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pipenv install
	@echo ""
	@echo "[OK] Dependencies installed"
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
	@echo "[OK] Cleanup complete"
