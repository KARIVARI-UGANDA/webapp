#!/bin/bash
set -e

echo ""
echo "=========================================="
echo "  Setting up Kari Vari Uganda"
echo "=========================================="

# Write Codespace secrets to .env so docker-compose and run.py can read them
echo ""
echo "-> Writing secrets to .env..."
printenv | grep -E 'DATABASE_URL|SECRET_KEY|STRIPE|FLUTTERWAVE|PAYSTACK|SMTP|RESEND' > .env
echo "   Done."

# Set up venv and install dependencies
echo ""
echo "-> Installing Python dependencies..."
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
echo "   Done."

echo ""
echo "=========================================="
echo "  Setup complete! Run the app with:"
echo ""
echo "    source venv/bin/activate && python run.py"
echo ""
echo "  Or with Docker:"
echo ""
echo "    docker compose up --build"
echo "=========================================="
echo ""
