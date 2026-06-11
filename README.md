# 🌿 Kari Vari Uganda

> **The easiest way to rent a premium 4×4 in Uganda.**
> We connect travellers with verified local car owners — fully online, fully trusted.

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-webapp--01os.onrender.com-blue?style=for-the-badge)](https://webapp-01os.onrender.com/)
[![CI](https://github.com/KARIVARI-UGANDA/webapp/actions/workflows/ci.yml/badge.svg)](https://github.com/KARIVARI-UGANDA/webapp/actions/workflows/ci.yml)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/KARIVARI-UGANDA/webapp)

---

## 🔗 Useful Links

| Link | Description |
|---|---|
| [Live App](https://webapp-01os.onrender.com/) | Production deployment |
| [Browse Vehicles](https://webapp-01os.onrender.com/vehicles) | See available 4×4s |
| [Customer Login](https://webapp-01os.onrender.com/login) | Log in as a customer — use the **Quick Access** button on the login page to enter without signing up |
| [Owner / Admin Login](https://webapp-01os.onrender.com/owner/login) | Log in as owner or admin — use the **Quick Access** button to log in instantly |
| [API Docs](https://webapp-01os.onrender.com/api/docs) | Interactive Swagger UI |
| [Health Check](https://webapp-01os.onrender.com/api/health) | Server status |

---

## 👥 Team

| Name | Role |
|---|---|
| George Mutale | Backend |
| Rhyan Lubega | Frontend |
| Oscar Kyamuwendo | Business |
| Boaz Onyango | Database · Security · Business |

---

## 🚀 Running the App

### ✅ Option 1 — GitHub Codespaces

Click the **Open in GitHub Codespaces** badge above and wait for setup to finish, then run:

```bash
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python run.py
```

Or with Docker (Codespaces has Docker built in):

```bash
docker compose up --build
```

---

### 💻 Option 2 — Local Python

Requires Python 3.11+. Clone the repo, then:

```bash
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python run.py
```

Windows:

```bash
python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python run.py
```

---

## 🌍 About Kari Vari Uganda

Uganda is one of East Africa's most breathtaking destinations — from the gorillas of Bwindi to the shores of Lake Victoria and the savannahs of Queen Elizabeth National Park. But getting there in comfort and safety has always been a challenge.

**Kari Vari Uganda** was built to change that. We are a marketplace that connects travellers directly with verified local 4×4 vehicle owners, cutting out middlemen and putting more money in the hands of Ugandan communities.

**What makes us different:**
- Every vehicle owner is verified before listing — ID, insurance, and vehicle inspection checks
- Customers can browse, book, and pay entirely online with Stripe, Paystack, or Flutterwave
- Transparent pricing — no hidden fees, no last-minute surprises
- Built and maintained by a team of students at the Technische Hochschule Deggendorf, Uganda

Whether you're planning a gorilla trekking safari, a cross-country road trip, or a weekend getaway, Kari Vari has the right vehicle for you.

---

## 🤝 Contribute & Work With Us

We welcome contributions from developers, designers, and travel enthusiasts!

- **Found a bug?** [Open an issue](https://github.com/KARIVARI-UGANDA/webapp/issues)
- **Have an idea?** [Start a discussion](https://github.com/KARIVARI-UGANDA/webapp/discussions)
- **Want to contribute?** Fork the repo, make your changes, and open a pull request — we review all PRs

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR-USERNAME/webapp.git
cd webapp
git checkout -b your-feature-branch
# make your changes
git push origin your-feature-branch
# open a Pull Request on GitHub
```

All skill levels welcome. If you're unsure where to start, check the [open issues](https://github.com/KARIVARI-UGANDA/webapp/issues) labelled `good first issue`.

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
├── run.py               # ← start here: python run.py
├── Dockerfile           # App container image
├── docker-compose.yml   # One-command Docker setup
└── requirements.txt     # Python dependencies
```

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
| Database | PostgreSQL 16 (Supabase) |
| ORM | SQLAlchemy 2.0 |
| Auth | JWT (PyJWT) · bcrypt |
| Payments | Stripe · Flutterwave · Paystack |
| Email | Resend API · SMTP |
| Frontend | Jinja2 · Tailwind CSS |
| Hosting | Render.com |
| CI/CD | GitHub Actions |
