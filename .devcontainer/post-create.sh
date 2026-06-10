#!/bin/bash
set -e

echo ""
echo "=========================================="
echo "  Setting up Kari Vari Uganda"
echo "=========================================="

# ── 1. Install Python dependencies ────────────────────────────────────────────
echo ""
echo "-> Installing Python dependencies..."
# Use pip3 explicitly — works reliably in Codespaces
pip3 install -r requirements.txt

echo "   Done."

# ── 2. Wait for PostgreSQL to be ready ────────────────────────────────────────
echo ""
echo "-> Waiting for PostgreSQL..."
for i in $(seq 1 30); do
  if pg_isready -U postgres -q 2>/dev/null; then
    echo "   PostgreSQL is ready."
    break
  fi
  echo "   Waiting... ($i/30)"
  sleep 2
done

# ── 3. Create the database ────────────────────────────────────────────────────
echo ""
echo "-> Creating database 'karivari'..."
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'karivari'" \
  | grep -q 1 || psql -U postgres -c "CREATE DATABASE karivari"
echo "   Database ready."

echo ""
echo "=========================================="
echo "  Setup complete! Run the app with:"
echo ""
echo "    python run.py"
echo ""
echo "  Demo accounts will be created on first run."
echo "=========================================="
echo ""
