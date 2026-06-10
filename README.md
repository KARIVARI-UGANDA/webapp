# 🌿 Kari Vari Uganda

Premium 4×4 vehicle rental marketplace connecting customers with verified Ugandan car owners.

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-webapp--01os.onrender.com-blue?style=for-the-badge)](https://webapp-01os.onrender.com/)
[![CI](https://github.com/KARIVARI-UGANDA/webapp/actions/workflows/ci.yml/badge.svg)](https://github.com/KARIVARI-UGANDA/webapp/actions/workflows/ci.yml)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/KARIVARI-UGANDA/webapp)

---

## ▶ Running the app

### Option 1 — GitHub Codespaces ✅ Easiest (nothing to install)

Click the button above, or go to the repo on GitHub → **Code → Codespaces → Create codespace on main**.

Codespaces will automatically:
- Start a Python 3.11 environment
- Install PostgreSQL 16 and create the database
- Install all Python dependencies

Once the setup finishes (about 2 minutes), run **one command** in the terminal:

```bash
python run.py
```

A browser preview opens automatically at your Codespace URL. Done.

**To run the tests:**
```bash
pytest tests/ -v
```

---

### Option 2 — Docker (local machine)

**Requires:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) — free, works on Windows, Mac, and Linux.

```bash
git clone https://github.com/KARIVARI-UGANDA/webapp.git
cd webapp
docker compose up --build
```

Open **http://localhost:8000** in your browser. Everything — app and database — starts automatically.

**To stop:**
```bash
Ctrl+C
docker compose down
```

**To reset the database and start fresh:**
```bash
docker compose down -v
docker compose up --build
```

---

### Option 3 — Python locally (no Docker)

**Requires:** Python 3.11 or 3.12

```bash
git clone https://github.com/KARIVARI-UGANDA/webapp.git
cd webapp

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env          # Mac / Linux
copy .env.example .env        # Windows

# Run
python run.py
```

Uses a local SQLite file (`karivari.db`) — no database installation needed.

Open **http://127.0.0.1:8000**

---

## Pages & URLs

| URL | Description |
|-----|-------------|
| `/` | Home page |
| `/vehicles` | Browse vehicles |
| `/login` | Customer login |
| `/owner/login` | Owner / admin login |
| `/api/docs` | Interactive API docs (Swagger UI) |
| `/api/redoc` | API reference (ReDoc) |
| `/api/health` | Health check |

---

## Running the tests

```bash
pip install -r requirements.txt pytest-cov

# Mac / Linux / Codespaces
DATABASE_URL=sqlite:///:memory: SECRET_KEY=test-secret-32-chars-longxxxxxx pytest tests/ -v

# Windows
set DATABASE_URL=sqlite:///:memory: && set SECRET_KEY=test-secret-32-chars-longxxxxxx && pytest tests/ -v
```

Expected: **121 passed**

---

## Project structure

```
webapp/
├── app/
│   ├── main.py          # FastAPI app + router registration
│   ├── config.py        # Settings loaded from environment variables
│   ├── database.py      # SQLAlchemy engine and session
│   ├── deps.py          # Auth / role dependencies
│   ├── security.py      # JWT token helpers
│   ├── models/          # Database table definitions (SQLAlchemy ORM)
│   ├── schemas/         # Request / response shapes (Pydantic)
│   ├── routers/         # API endpoints (auth, bookings, vehicles, …)
│   └── services/        # Email, Stripe, Flutterwave, Paystack
├── tests/               # 121 automated tests (pytest)
├── static/              # CSS, JS, images
├── templates/           # HTML pages (Jinja2 + Tailwind CSS)
├── .devcontainer/       # GitHub Codespaces configuration
├── run.py               # Entry point — python run.py
├── Dockerfile           # App container image
├── docker-compose.yml   # App + Postgres (one command)
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variable template
```

---

## Environment variables

Copy `.env.example` to `.env` to configure the app.
Payment and email are **optional** — they silently skip when not configured so the app runs fine for a demo.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Auto-set in Codespaces and Docker. Use `sqlite:///./karivari.db` locally. |
| `SECRET_KEY` | Yes | Any random string of 32+ characters |
| `STRIPE_SECRET_KEY` | Optional | Card payments |
| `FLUTTERWAVE_SECRET_KEY` | Optional | MTN / Airtel mobile money |
| `SMTP_HOST` + `SMTP_PASSWORD` | Optional | Transactional emails |

---

## CI/CD Pipeline

Every push to `main` runs automatically on GitHub Actions:

| Job | What it does |
|---|---|
| **Lint & format** | `ruff check` + `ruff format --check` |
| **Security scan** | `bandit` static analysis + `safety` CVE check |
| **Tests** | 121 tests on Python 3.11 and 3.12 |
| **Deploy** | Triggers Render deploy — only after all tests pass |

**To publish a release** (auto-generates changelog):
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Database | PostgreSQL 16 (Codespaces / Docker / production) · SQLite (local) |
| ORM | SQLAlchemy 2.0 |
| Auth | JWT (python-jose) · bcrypt passwords |
| Payments | Stripe · Flutterwave · Paystack |
| Email | Resend API · SMTP fallback |
| Frontend | Jinja2 templates · Tailwind CSS |
| Hosting | Render.com |
| CI/CD | GitHub Actions |

---

## Team

| Name | Role |
|---|---|
| George Mutale | Backend & DevOps |
| Oscar Kyamuwendo | Frontend & UI |
| Utman (Rhyan2) | Backend & Integration |
