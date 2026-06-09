# Karivari Uganda — Verified 4×4 Safaris with Owner-Drivers

> Connect with verified Ugandan owner-drivers. Book a 4×4 for your safari with one all-in daily rate.

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-webapp--01os.onrender.com-blue?style=for-the-badge)](https://webapp-01os.onrender.com/)

---

## Table of Contents

1. [About](#-about-karivari-uganda)
2. [Who It's For](#-whos-it-for)
3. [Key Features](#-key-features)
4. [Quick Start](#-quick-start)
5. [Project Structure](#-project-structure)
6. [API Reference](#-api-reference)
7. [Tech Stack](#️-tech-stack)
8. [Configuration](#-environment-configuration)
9. [Testing](#-testing)
10. [Deployment](#-deployment)
11. [Contributing](#-contributing)
12. [Support](#-support)

---

## 🎯 About Karivari Uganda

Karivari Uganda is a trusted marketplace connecting travellers with verified local owner-drivers for 4×4 safaris across Uganda. Whether you're tracking gorillas in Bwindi, photographing wildlife in Queen Elizabeth Park, or heading into the Albertine Rift, every booking comes with a verified vehicle, a German-speaking driver, and one daily rate that covers everything.

**Live platform:** [https://webapp-01os.onrender.com/](https://webapp-01os.onrender.com/)  
No sign-up required to browse. Create an account in seconds to book or list a vehicle.

---

## 👥 Who's It For

| User | Description |
|------|-------------|
| 📷 **Photography Travellers** | Open-roof vehicles, early starts, owner-drivers who understand light and patience. Trips typically run 10–14 days. |
| 🌿 **Wildlife & Safari Travellers** | Gorilla tracking, big game in the savannah parks, and birding along the Albertine Rift. Drivers who double as guides. |
| 🏨 **Luxury Travellers** | Booking premium lodges who expect their transport to match. Quiet vehicles, polished service, end-to-end itinerary coordination. |
| 🚗 **Owner-Drivers** | Verified local drivers who own their vehicle. List your 4×4, set your availability, and keep the majority of every daily rate. |
| 🏢 **Travel Agencies & Partners** | German-speaking agencies and lodge partners who need a reliable, pre-vetted transport layer for Uganda itineraries. |
| 🛡️ **Karivari Admins** | Verify vehicles and owner-drivers, manage bookings, handle KYC, and monitor the platform. |

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔐 **KYC Verification** | All owner-drivers are verified before their first trip |
| 💳 **Multi-Payment** | Stripe (cards), Paystack, Flutterwave (mobile money) |
| 📅 **Flexible Booking** | Reserve with flexible dates and free cancellation up to 7 days before pickup |
| 🛡️ **Insurance Included** | Every booking includes comprehensive CDW coverage |
| 💬 **Direct Messaging** | Chat with your owner-driver before and during the trip |
| ⭐ **Reviews & Ratings** | Transparent feedback on every vehicle and driver |
| 📊 **Earnings Dashboard** | Owner-drivers track income and booking history |
| 📱 **Real-time Notifications** | Instant updates on booking and trip status |
| 🚫 **Dispute Resolution** | Fair process for handling issues on either side |

### Pricing Model

- Owner-drivers keep **95%** of the booking price (5% platform fee)
- Fixed insurance: **$15 per booking**
- Free cancellation up to **7 days** before pickup

---

## ⚡ Quick Start

### Option 1 — Run Locally

**Prerequisites:** Python 3.11+, pip, git

```bash
# Clone the repository
git clone https://github.com/yourusername/karivari-uganda.git
cd karivari-uganda

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
UVICORN_RELOAD=1 python run.py
```

Open [http://localhost:8000/](http://localhost:8000/) in your browser.

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/` | Web app |
| `http://localhost:8000/api/docs` | Swagger API docs |
| `http://localhost:8000/api/redoc` | ReDoc API docs |

---

### Option 2 — GitHub Codespaces

1. Click **Code** on GitHub → **Codespaces** → **Create codespace on main**
2. Wait ~30 seconds for setup
3. In the terminal:

```bash
pip install -r requirements.txt && UVICORN_RELOAD=1 python run.py
```

4. Click **Open in Browser** when the port-forwarding popup appears

Codespaces gives you a zero-setup Python 3.11 environment with automatic port forwarding, shareable preview URLs, and 120 free core hours per month.

---

### Option 3 — Docker

```bash
docker build -t karivari-webapp . && docker run --rm -p 8000:8000 karivari-webapp
```

---

## 📂 Project Structure

```
webapp/
├── app/
│   ├── main.py              # FastAPI app initialisation
│   ├── config.py            # Settings & environment config
│   ├── database.py          # Database connection
│   ├── deps.py              # Dependency injection (auth, roles)
│   ├── security.py          # JWT & password hashing
│   ├── models/              # SQLAlchemy models (User, Vehicle, Booking …)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py          # Login, register, token refresh
│   │   ├── users.py         # User profile management
│   │   ├── vehicles.py      # Vehicle listings
│   │   ├── bookings.py      # Booking lifecycle
│   │   ├── payments.py      # Payment processing & webhooks
│   │   ├── reviews.py       # Reviews & ratings
│   │   ├── messages.py      # Owner-traveller messaging
│   │   └── admin.py         # Admin dashboard & KYC
│   ├── services/            # Business logic layer
│   ├── templates/           # Jinja2 HTML templates
│   ├── static/              # CSS, JS, images
│   └── uploads/             # User-uploaded files
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container configuration
└── README.md
```

---

## 🚀 API Reference

Full interactive docs available at `/api/docs` when the app is running.

### Authentication

```
POST   /api/auth/register        Create account
POST   /api/auth/login           Sign in
POST   /api/auth/refresh         Refresh access token
POST   /api/auth/logout          Sign out
```

### Vehicles

```
GET    /api/vehicles             List all vehicles
POST   /api/vehicles             Create listing (owner)
GET    /api/vehicles/{id}        Get vehicle details
PUT    /api/vehicles/{id}        Update listing
DELETE /api/vehicles/{id}        Remove listing
```

### Bookings

```
GET    /api/bookings             My bookings
POST   /api/bookings             Create booking
GET    /api/bookings/{id}        Get booking details
PUT    /api/bookings/{id}        Modify booking
DELETE /api/bookings/{id}        Cancel booking
```

### Payments

```
POST   /api/payments/initiate    Start payment
GET    /api/payments/{id}        Payment status
POST   /api/payments/webhook     Provider webhook handler
```

### Other

```
GET    /api/users/me             My profile
GET/POST /api/reviews            Ratings & feedback
GET/POST /api/messages           Owner-traveller chat
GET    /api/admin/dashboard      Platform metrics (admin only)
GET    /api/health               Health check
```

---

## 🏗️ Tech Stack

### Backend
| Library | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.115.0 | Web framework & API |
| SQLAlchemy | 2.0 | ORM & database management |
| SQLite | — | Development database |
| PyJWT | — | Token-based authentication |
| bcrypt | — | Password hashing |

### Frontend
| Tool | Purpose |
|------|---------|
| Jinja2 | Server-side HTML templating |
| Bootstrap 5 | Responsive CSS framework |
| Vanilla JS | Client-side interactivity |

### Payment Providers
| Provider | Use Case |
|----------|---------|
| Stripe | International card payments |
| Paystack | African card & bank payments |
| Flutterwave | Mobile money (MTN, Airtel Uganda) |

---

## 📝 Environment Configuration

Create a `.env` file in the project root:

```env
# Security
SECRET_KEY=change-me-to-32-random-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14

# CORS
CORS_ORIGINS=http://localhost:8000,http://localhost:8080

# Stripe
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY
STRIPE_CURRENCY=usd

# Flutterwave
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST_YOUR_KEY
FLUTTERWAVE_PUBLIC_KEY=FLWPUBK_TEST_YOUR_KEY

# Paystack
PAYSTACK_SECRET_KEY=sk_test_YOUR_KEY
PAYSTACK_PUBLIC_KEY=pk_test_YOUR_KEY

# Business Rules
INSURANCE_FLAT_FEE_USD=15.0
BOOKING_HOLD_MINUTES=30
CANCELLATION_FREE_DAYS=7
CANCELLATION_HALF_REFUND_DAYS=2
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Specific file
pytest tests/test_auth.py

# With coverage report
pytest --cov=app
```

---

## 🌍 Deployment

The platform is deployed on **Render.com**:  
🔗 [https://webapp-01os.onrender.com/](https://webapp-01os.onrender.com/)

### Deploy Your Own Instance

1. Sign up at [render.com](https://render.com)
2. Connect your GitHub repository → **Web Service**
3. Set runtime to **Docker**, port **8000**
4. Add environment variables from the `.env` template above
5. Click **Deploy** — Render redeploys automatically on every push to `main`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and run tests: `pytest`
4. Commit: `git commit -m "Add your feature"`
5. Push and open a Pull Request

### Code Standards
- Follow PEP 8
- Use type hints throughout
- Keep functions focused — business logic belongs in `services/`, not routers

---

## 🐛 Troubleshooting

**Port 8000 already in use**
```bash
python run.py --port 8001
```

**Dependencies won't install**
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**Database issues**
```bash
rm karivari.db
python run.py
```

**Docker build fails**
```bash
docker system prune -a
docker build -t karivari-webapp .
```

---

## 📞 Support.

- **API reference** — `/api/docs` (running locally) or the live demo URL
- **Bug reports** — Open a GitHub issue
- **Partnership enquiries** — [webapp-01os.onrender.com/support](https://webapp-01os.onrender.com/support)
- **Apply as an owner-driver** — [webapp-01os.onrender.com/owner/register](https://webapp-01os.onrender.com/owner/register)

---

**Version:** 1.0.0 &nbsp;|&nbsp; **Status:** 🟢 Active &nbsp;|&nbsp; **Last updated:** June 2026
