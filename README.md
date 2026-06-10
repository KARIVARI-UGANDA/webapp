# 🌿 Kari Vari Uganda

Premium 4×4 vehicle rental marketplace connecting customers with verified Ugandan car owners.

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-webapp--01os.onrender.com-blue?style=for-the-badge)](https://webapp-01os.onrender.com/)
[![CI](https://github.com/KARIVARI-UGANDA/webapp/actions/workflows/ci.yml/badge.svg)](https://github.com/KARIVARI-UGANDA/webapp/actions/workflows/ci.yml)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/KARIVARI-UGANDA/webapp)

---

## 🚀 Running the App

### ✅ Option 1 — GitHub Codespaces (nothing to install)

1. Click the **Open in GitHub Codespaces** badge above
2. Wait ~2 minutes for setup to complete
3. In the terminal that opens, run:

```bash
python run.py
```

A browser preview opens automatically. Then seed the demo accounts:

```bash
python seed.py
```

---

### ✅ Option 2 — Uvicorn (Local Python)

Start the app:

```bash
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

```bash
DATABASE_URL=sqlite:///./karivari.db SECRET_KEY=local-dev-secret-32-chars-xxxx python run.py
```

Seed the demo accounts (in a second terminal with the same env vars set):

```bash
DATABASE_URL=sqlite:///./karivari.db SECRET_KEY=local-dev-secret-32-chars-xxxx python seed.py
```

**Super Admin Sign-In:**

| Field | Value |
|-------|-------|
| Email | `george.mutale345@stud.th-deg.de` |
| Password | `Administer01@#` |

**Admin Sign-In:**

| Field | Value |
|-------|-------|
| Email | `mutalegeorge367@gmail.com` |
| Password | `Operator02@#` |

**Customer Sign-In:**

| Field | Value |
|-------|-------|
| Email | `george.mutale@stud.th-deg.de` |
| Password | `Tourist01@#` |

---

### 🐳 Option 3 — Docker

Docker creates a separate database. Run `seed.py` after startup to create demo accounts.

Build and run the services:

```bash
chmod +x start.sh
./start.sh
```

Or on Windows:

```bash
docker compose up --build
```

Once running, open a new terminal and seed the demo accounts:

```bash
docker compose exec web python seed.py
```

**Customer Sign-Up / Login:**
Use the app interface to register and log in, or use the seeded accounts above.

Stop the services:

```bash
Ctrl + C
```

```bash
# Or stop the container manually
docker ps
docker stop <container_id>
```

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
pip install -r requirements.txt pytest-cov

# Mac / Linux / Codespaces
DATABASE_URL=sqlite:///:memory: SECRET_KEY=test-secret-32-chars-longxxxxxx pytest tests/ -v

# Windows
set DATABASE_URL=sqlite:///:memory: && set SECRET_KEY=test-secret-32-chars-longxxxxxx && pytest tests/ -v
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
├── run.py               # Entry point — python run.py
├── seed.py              # Creates demo accounts in the database
├── start.sh             # Docker shortcut — ./start.sh
├── Dockerfile           # App container image
├── docker-compose.yml   # App + Postgres (one command)
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variable template
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` to configure the app.
Payment and email are **optional** — the app runs fine for a demo without any API keys.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Auto-set in Codespaces and Docker. Use `sqlite:///./karivari.db` locally. |
| `SECRET_KEY` | Yes | Any random string of 32+ characters |
| `STRIPE_SECRET_KEY` | Optional | Card payments |
| `FLUTTERWAVE_SECRET_KEY` | Optional | MTN / Airtel mobile money |
| `SMTP_HOST` + `SMTP_PASSWORD` | Optional | Transactional emails |

---

## 🔄 CI/CD Pipeline

Every push to `main` runs automatically:

| Job | What it does |
|---|---|
| **Lint & format** | `ruff check` + `ruff format --check` |
| **Security scan** | `bandit` static analysis + `safety` CVE check |
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
| Database | PostgreSQL 16 (Codespaces / Docker / production) · SQLite (local) |
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
