# 🌿 Kari Vari Uganda

Premium 4×4 vehicle rental marketplace connecting customers with verified Ugandan car owners.

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-webapp--01os.onrender.com-blue?style=for-the-badge)](https://webapp-01os.onrender.com/)
[![CI](https://github.com/KARIVARI-UGANDA/webapp/actions/workflows/ci.yml/badge.svg)](https://github.com/KARIVARI-UGANDA/webapp/actions/workflows/ci.yml)

---

## Running the app (one command)

### Option 1 — Docker ✅ Recommended

**Requires:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) — free, works on Windows, Mac, and Linux.

```bash
docker compose up --build
```

That's it. Docker will automatically:
- Start a **PostgreSQL 16** database
- Install all Python dependencies
- Start the web server

Then open: **http://localhost:8000**

| URL | What it is |
|-----|------------|
| http://localhost:8000 | Main website |
| http://localhost:8000/api/docs | Interactive API documentation (Swagger UI) |
| http://localhost:8000/api/redoc | API reference (ReDoc) |
| http://localhost:8000/api/health | Health check |

**To stop the app:**
```bash
Ctrl+C
docker compose down
```

**To reset the database and start completely fresh:**
```bash
docker compose down -v
docker compose up --build
```

---

### Option 2 — Python locally (no Docker)

**Requires:** Python 3.11 or 3.12

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy the environment template
cp .env.example .env          # Mac / Linux
copy .env.example .env        # Windows

# 3. Start the app
python run.py
```

This uses a local **SQLite** file (`karivari.db`) — no database installation needed.

Then open: **http://127.0.0.1:8000**

---

## Running the tests

```bash
pip install -r requirements.txt pytest-cov

# Windows
set DATABASE_URL=sqlite:///:memory: && set SECRET_KEY=test-secret-key-32-chars-longxx && pytest tests/ -v

# Mac / Linux
DATABASE_URL=sqlite:///:memory: SECRET_KEY=test-secret-key-32-chars-longxx pytest tests/ -v
```

Expected output: **121 passed**

---

## Project structure

```
webapp/
├── app/
│   ├── main.py          # FastAPI application + router registration
│   ├── config.py        # All settings loaded from environment variables
│   ├── database.py      # SQLAlchemy engine and session
│   ├── deps.py          # Auth / role dependencies
│   ├── security.py      # JWT token helpers
│   ├── models/          # Database table definitions (SQLAlchemy ORM)
│   ├── schemas/         # Request / response data shapes (Pydantic)
│   ├── routers/         # API endpoints (auth, bookings, vehicles, …)
│   └── services/        # Email, Stripe, Flutterwave, Paystack integrations
├── tests/               # 121 automated tests (pytest)
├── static/              # CSS, JS, images
├── templates/           # HTML pages (Jinja2 + Tailwind CSS)
├── run.py               # ← start here:  python run.py
├── Dockerfile           # App container image
├── docker-compose.yml   # App + Postgres (one command setup)
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variable template
```

---

## Environment variables

Copy `.env.example` to `.env` to configure the app.
Payment and email features are **optional** — they silently skip when keys are not set, so the app runs normally for a demo without any API keys.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Set automatically by Docker; use `sqlite:///./karivari.db` locally |
| `SECRET_KEY` | Yes | Any random string of 32+ characters |
| `STRIPE_SECRET_KEY` | Optional | Card payments (Stripe test key works) |
| `FLUTTERWAVE_SECRET_KEY` | Optional | MTN / Airtel mobile money |
| `SMTP_HOST` + `SMTP_PASSWORD` | Optional | Transactional emails |

---

## CI/CD Pipeline

Every push to `main` runs the full pipeline automatically:

| Job | What it does |
|---|---|
| **Lint & format** | Code style (`ruff check`) + formatting (`ruff format`) |
| **Security scan** | Static analysis (`bandit`) + known CVEs (`safety`) |
| **Tests** | 121 pytest tests on Python 3.11 and 3.12 |
| **Deploy** | Triggers Render deploy — only runs after all tests pass |

**To publish a numbered release** (creates a GitHub Release with changelog):
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Database | PostgreSQL 16 (Docker / production) · SQLite (local) |
| ORM | SQLAlchemy 2.0 |
| Auth | JWT via python-jose · passwords via bcrypt |
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
