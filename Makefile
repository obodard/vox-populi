.PHONY: install clean

# Install all dependencies
install:
	@echo "Installing nemo_toolkit..."
	pip install nemo_toolkit --no-deps
	@echo "Installing requirements from requirements.txt..."
	pip install -r requirements.txt
	@echo "Installing texterrors..."
	pip install --only-binary=:all: texterrors
	@echo "✓ All dependencies installed successfully"

# Clean Python cache files
clean:
	@echo "Cleaning Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned successfully"

