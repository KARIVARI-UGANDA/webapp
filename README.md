# 🌿 Kari Vari Uganda

Premium 4×4 vehicle rental marketplace connecting customers with verified Ugandan car owners.

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-webapp--01os.onrender.com-blue?style=for-the-badge)](https://webapp-01os.onrender.com/)
[![CI](https://github.com/KARIVARI-UGANDA/webapp/actions/workflows/ci.yml/badge.svg)](https://github.com/KARIVARI-UGANDA/webapp/actions/workflows/ci.yml)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/KARIVARI-UGANDA/webapp)

---

## 🚀 Running the App

### ✅ Option 1 — GitHub Codespaces (nothing to install)

Click the **Open in GitHub Codespaces** badge above, wait ~2 minutes for setup to finish, then run:

```bash
python run.py
```

That's it. The app creates the database, seeds demo accounts, and starts the server automatically.

> **If you see a "No module named" error**, run this once first:
> ```bash
> pip3 install -r requirements.txt && python run.py
> ```

---

### ✅ Option 2 — Uvicorn (Local Python)

Requires Python 3.11+. One command:

```bash
python run.py
```

No database setup needed — uses a local SQLite file automatically.

---

### 🐳 Option 3 — Docker

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/). One command:

```bash
docker compose up --build
```

Starts PostgreSQL and the app together. Everything — database, tables, and demo accounts — is set up automatically.

Stop the services:

```bash
Ctrl + C
docker compose down
```

Reset the database and start fresh:

```bash
docker compose down -v
docker compose up --build
```

---

## 🔑 Demo Accounts

These are created automatically when the app starts.

**Super Admin**

| Field | Value |
|-------|-------|
| Email | `george.mutale345@stud.th-deg.de` |
| Password | `Administer01@#` |

**Admin**

| Field | Value |
|-------|-------|
| Email | `mutalegeorge367@gmail.com` |
| Password | `Operator02@#` |

**Customer**

| Field | Value |
|-------|-------|
| Email | `george.mutale@stud.th-deg.de` |
| Password | `Tourist01@#` |

Login at `/owner/login` for admin accounts, `/login` for customers.

---

## 📄 Pages & URLs

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Home page |
| `http://localhost:8000/vehicles` | Browse vehicles |
| `http://localhost:8000/login` | Customer login |
| `http://localhost:8000/owner/login` | Owner / Admin login |
| `http://localhost:8000/api/docs` | Interactive API docs (Swagger UI) |
| `http://localhost:8000/api/health` | Health check |

---

## 🧪 Running the Tests

```bash
pytest tests/ -v
```

Expected: **121 passed**

---

## 📁 Project Structure

```
webapp/
├── app/
│   ├── main.py          # FastAPI app + router registration
│   ├── config.py        # Settings loaded from environment variables
│   ├── database.py      # SQLAlchemy engine and session
│   ├── deps.py          # Auth / role dependencies
│   ├── security.py      # JWT helpers + password hashing
│   ├── models/          # Database table definitions (SQLAlchemy ORM)
│   ├── schemas/         # Request / response shapes (Pydantic)
│   ├── routers/         # API endpoints (auth, bookings, vehicles, …)
│   └── services/        # Email, Stripe, Flutterwave, Paystack
├── tests/               # 121 automated tests (pytest)
├── static/              # CSS, JS, images
├── templates/           # HTML pages (Jinja2 + Tailwind CSS)
├── .devcontainer/       # GitHub Codespaces configuration
├── run.py               # ← start here: python run.py
├── Dockerfile           # App container image
├── docker-compose.yml   # App + Postgres (one command)
└── requirements.txt     # Python dependencies
```

---

## ⚙️ Environment Variables

All optional — `run.py` sets safe defaults automatically. To override, create a `.env` file based on `.env.example`.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./karivari.db` | PostgreSQL or SQLite URL |
| `SECRET_KEY` | auto (dev only) | JWT signing key — **change in production** |
| `STRIPE_SECRET_KEY` | *(empty)* | Card payments — skipped if not set |
| `FLUTTERWAVE_SECRET_KEY` | *(empty)* | Mobile money — skipped if not set |
| `SMTP_HOST` | *(empty)* | Email sending — skipped if not set |

---

## 🔄 CI/CD Pipeline

Every push to `main` runs automatically:

| Job | What it does |
|---|---|
| **Lint & format** | `ruff check` + `ruff format --check` |
| **Security scan** | `bandit` + `safety` CVE check |
| **Tests** | 121 tests on Python 3.11 and 3.12 |
| **Deploy** | Triggers Render deploy — only after all tests pass |

**To publish a release:**
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Database | PostgreSQL 16 (Docker / production) · SQLite (local) |
| ORM | SQLAlchemy 2.0 |
| Auth | JWT (python-jose) · bcrypt |
| Payments | Stripe · Flutterwave · Paystack |
| Email | Resend API · SMTP |
| Frontend | Jinja2 · Tailwind CSS |
| Hosting | Render.com |
| CI/CD | GitHub Actions |

---

## 👥 Team

| Name | Role |
|---|---|
| George Mutale | Backend & DevOps |
| Oscar Kyamuwendo | Frontend & UI |
| Utman (Rhyan2) | Backend & Integration |
