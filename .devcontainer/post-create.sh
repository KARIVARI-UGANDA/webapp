#!/bin/bash
set -e

echo ""
echo "=========================================="
echo "  Setting up Kari Vari Uganda"
echo "=========================================="

# Set up venv and install dependencies
echo ""
echo "-> Installing Python dependencies..."
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
echo "   Done."

echo ""
echo "=========================================="
echo "  Setup complete! Run the app with:"
echo ""
echo "    python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python run.py"
echo "=========================================="
echo ""
