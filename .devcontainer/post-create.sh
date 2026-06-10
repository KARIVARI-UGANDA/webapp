#!/bin/bash
set -e

echo ""
echo "=========================================="
echo "  Setting up Kari Vari Uganda dev environment"
echo "=========================================="

# ── 1. Install Python dependencies ────────────────────────────────────────────
echo ""
echo "→ Installing Python dependencies..."
pip install -r requirements.txt --quiet

# ── 2. Wait for PostgreSQL to be ready ────────────────────────────────────────
echo ""
echo "→ Waiting for PostgreSQL..."
for i in $(seq 1 20); do
  if pg_isready -U postgres -q; then
    echo "  PostgreSQL is ready."
    break
  fi
  echo "  Waiting... ($i/20)"
  sleep 2
done

# ── 3. Create the database (safe to re-run) ───────────────────────────────────
echo ""
echo "→ Creating database 'karivari'..."
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'karivari'" \
  | grep -q 1 || psql -U postgres -c "CREATE DATABASE karivari"
echo "  Database ready."

echo ""
# ── 4. Seed demo accounts ─────────────────────────────────────────────────────
echo ""
echo "→ Seeding demo accounts..."
python seed.py

echo "=========================================="
echo "  ✅ Setup complete!"
echo ""
echo "  Start the app:"
echo "    python run.py"
echo ""
echo "  Demo accounts (seeded and ready):"
echo "    Super Admin : george.mutale345@stud.th-deg.de / Administer01@#"
echo "    Admin       : mutalegeorge367@gmail.com       / Operator02@#"
echo "    Customer    : george.mutale@stud.th-deg.de    / Tourist01@#"
echo ""
echo "  Run tests:"
echo "    pytest tests/ -v"
echo "=========================================="
echo ""
