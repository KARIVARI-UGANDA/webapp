# Karivari Uganda - 4×4 Vehicle Marketplace

> **Connect with verified Ugandan car owners. Rent or buy 4×4 vehicles with confidence.**

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-webapp--01os.onrender.com-blue?style=for-the-badge)](https://webapp-01os.onrender.com/)

Experience the platform instantly: **[https://webapp-01os.onrender.com/](https://webapp-01os.onrender.com/)**

---

## 🎯 About Karivari Uganda

Karivari Uganda is a trusted marketplace revolutionizing how customers and vehicle owners connect in Uganda. Whether you're looking to rent a reliable 4×4 for your next adventure or list your vehicle to earn extra income, we've got you covered.

### Why Choose Karivari?
✅ Verified Owners — All vehicle owners undergo KYC verification
✅ Secure Transactions — Multiple payment options (Stripe, Paystack, Flutterwave)
✅ Flexible Booking — Reserve vehicles with 7-day free cancellation
✅ 24/7 Support — Message owners directly, track your trip in real-time
✅ Insurance Included — Every booking includes comprehensive coverage
✅ Transparent Pricing — No hidden fees, fixed insurance of $15 per booking

### Who It's For
📷 **Photography Travellers** — Open-roof vehicles, early starts, owner-drivers who understand light and patience. Trips typically run 10–14 days.
🌿 **Wildlife & Safari Travellers** — Gorilla tracking, big game in the savannah parks, and birding along the Albertine Rift. Drivers who double as guides.
🏨 **Luxury Travellers** — Booking premium lodges and expect transport to match. Quiet vehicles, polished service, end-to-end coordination with your itinerary.
🚗 **Owner-Drivers** — Verified local drivers who own their vehicle. List your 4×4, set your availability, and keep the majority of every daily rate.
🏢 **Travel Agencies & Partners** — German-speaking agencies and lodge partners who want a reliable, pre-vetted transport layer for their Uganda itineraries.
🛡️ **Karivari Admins** — Verify vehicles and owner-drivers, manage bookings, handle KYC, and monitor the platform.

---

## 📱 Live Demo - Try It Now!

**🔗 [webapp-01os.onrender.com](https://webapp-01os.onrender.com/)**

No sign-up required to browse. Create an account in seconds to start booking or listing vehicles.

---

## ⚡ Quick Start

### Option 1: Run Locally (2 minutes)

#### Prerequisites
- Python 3.11+
- pip and git

#### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/karivari-uganda.git
cd karivari-uganda

# 2. Create virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
UVICORN_RELOAD=1 python run.py
```

✅ **Done!** Open your browser and go to **http://localhost:8000/**

- 🌐 Web App: http://localhost:8000/
- 📚 API Docs: http://localhost:8000/api/docs
- 📖 ReDoc: http://localhost:8000/api/redoc

---

### Option 2: GitHub Codespaces (No Installation!)

#### The Easiest Way - Code in the Cloud

1. Click the **Code** button on GitHub
2. Select **Codespaces** → **Create codespace on main**
3. Wait 30 seconds for setup
4. In the terminal, paste:

```bash
pip install -r requirements.txt && UVICORN_RELOAD=1 python run.py
```

5. Click the popup that says **Open in Browser** or visit the forwarded port

✨ **That's it!** Codespaces gives you:
- ☁️ Zero setup — pre-configured Python 3.11 environment
- 🔗 Automatic port forwarding — live preview URL
- 👥 Shareable links — show teammates your work instantly
- 💾 Auto-save — your code is always backed up
- 🚀 Free tier — 120 core hours/month included

---

### Option 3: Docker (One Command)

```bash
docker build -t karivari-webapp . && docker run --rm -p 8000:8000 karivari-webapp
```

---

## 📊 Project Overview

### The Platform at a Glance

Karivari Uganda is built as a **modern, full-featured marketplace** with:

#### 👥 **Three User Roles**
- **Customers** — Browse vehicles, make bookings, manage reservations
- **Vehicle Owners** — List vehicles, accept bookings, track earnings
- **Admins** — Monitor platform health, manage disputes, view analytics

#### 🎨 **Key Features**

| Feature | Description |
|---------|-------------|
| 🚗 **Vehicle Listings** | Browse 4×4 inventory with photos, ratings, pricing |
| 📅 **Smart Booking** | Reserve with flexible dates and auto-price calculation |
| 💳 **Multi-Payment** | Stripe (cards), Paystack, Flutterwave (mobile money) |
| 🛡️ **Insurance** | Automatic $15 coverage on every booking |
| 💬 **Live Messaging** | Chat directly with owners before booking |
| ⭐ **Reviews & Ratings** | Build trust through transparent feedback |
| 🚫 **Disputes** | Fair resolution process for issues |
| 📊 **Analytics** | Owners see earnings, customers see booking history |
| 🔐 **KYC Verification** | All users verified for safety |
| 📱 **Real-time Notifications** | Instant updates on booking status |

#### 💰 **Pricing Model**
- **Owners earn 95%** of booking price (5% platform fee)
- **Insurance:** $15 flat per booking
- **Flexible cancellation:** Free up to 7 days before pickup

---

## 🏗️ Tech Stack

### Backend
- **FastAPI 0.115.0** — Modern, fast Python framework
- **SQLAlchemy 2.0** — Robust ORM for data management
- **SQLite** — Local development database
- **JWT Authentication** — Secure token-based auth
- **bcrypt** — Industry-standard password hashing

### Frontend
- **Jinja2 Templates** — Dynamic HTML rendering
- **Bootstrap 5** — Responsive CSS framework
- **Vanilla JavaScript** — Interactive client-side features

### External Services
- **Stripe** — International credit card payments
- **Paystack** — African payment processing
- **Flutterwave** — Mobile money (MTN, Airtel Uganda)

---

## 📂 Project Structure

```
webapp/
├── app/
│   ├── main.py              # FastAPI initialization
│   ├── config.py            # Configuration & settings
│   ├── database.py          # Database connection
│   ├── models/              # Database models (User, Vehicle, Booking, etc.)
│   ├── schemas/             # Pydantic validation schemas
│   ├── routers/             # API endpoints
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── users.py         # User management
│   │   ├── vehicles.py      # Vehicle listings
│   │   ├── bookings.py      # Booking management
│   │   ├── payments.py      # Payment processing
│   │   ├── reviews.py       # Reviews & ratings
│   │   ├── messages.py      # Messaging system
│   │   ├── admin.py         # Admin dashboard
│   │   └── ...
│   ├── services/            # Business logic
│   ├── templates/           # HTML pages (Jinja2)
│   ├── static/              # CSS, JS, images
│   └── uploads/             # User-uploaded files
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container configuration
└── README.md                # Documentation
```

---

## 🚀 API Endpoints

The app provides a comprehensive REST API for all features.

### Authentication
```
POST   /api/auth/login          - Sign in
POST   /api/auth/register       - Create account
POST   /api/auth/refresh        - Get new token
POST   /api/auth/logout         - Sign out
```

### Vehicles
```
GET    /api/vehicles            - List all vehicles
POST   /api/vehicles            - Create listing
GET    /api/vehicles/{id}       - Get details
PUT    /api/vehicles/{id}       - Update listing
DELETE /api/vehicles/{id}       - Remove listing
```

### Bookings
```
GET    /api/bookings            - My bookings
POST   /api/bookings            - Create booking
GET    /api/bookings/{id}       - Get details
PUT    /api/bookings/{id}       - Modify booking
DELETE /api/bookings/{id}       - Cancel booking
```

### Payments
```
POST   /api/payments/initiate   - Start payment
GET    /api/payments/{id}       - Payment status
POST   /api/payments/webhook    - Webhook handler
```

### More
- `/api/users/me` — My profile
- `/api/reviews` — Ratings & feedback
- `/api/messages` — Chat with owners
- `/api/admin/dashboard` — Metrics & management

**📚 Full documentation:** Visit `/api/docs` when running the app

---

## 🤝 Team & Contributors

This project is built and maintained by:

| Role | Responsibility |
|------|-----------------|
| **Backend Lead** | FastAPI, databases, API design |
| **Frontend Developer** | UI/UX, templates, styling |
| **Payment Specialist** | Stripe, Paystack, Flutterwave integration |
| **QA Engineer** | Testing, bug fixes, quality assurance |

*Adding your name? [Contribute to the project!](#contributing)*

---

## 📝 Environment Configuration

Create a `.env` file with your settings:

```env
# Server
SECRET_KEY=change-me-to-32-random-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14

# CORS Origins (allow these domains)
CORS_ORIGINS=http://localhost:8000,http://localhost:8080

# Stripe (Card Payments)
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY
STRIPE_CURRENCY=usd

# Flutterwave (Mobile Money)
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

Run the test suite:

```bash
# All tests
pytest

# Verbose output
pytest -v

# Specific file
pytest tests/test_auth.py

# With coverage
pytest --cov=app
```

---

## 🐛 Troubleshooting

### Port 8000 Already in Use
```bash
python run.py --port 8001
```

### Dependencies Won't Install
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Database Issues
```bash
rm karivari.db  # Delete and recreate
python run.py
```

### Docker Build Fails
```bash
docker system prune -a
docker build -t karivari-webapp .
```

---

## 🌍 Production Deployment

The app is currently deployed on **Render.com** at:

🔗 **[https://webapp-01os.onrender.com/](https://webapp-01os.onrender.com/)**

### Deploying Your Own Instance

1. **Sign up at** [render.com](https://render.com)
2. **Connect your GitHub repo** → Web Service
3. **Configure:**
   - Environment: Docker
   - Port: 8000
4. **Set environment variables** (Dashboard → Environment)
5. **Click Deploy** — Automatic redeploy on push to main

---

## 📚 Documentation

- **API Docs** (Swagger): `/api/docs`
- **ReDoc** (Alternative): `/api/redoc`
- **Health Check**: `/api/health`
- **Home Page**: `/`

---

## 💡 For Developers

### Code Style
- Follow PEP 8 Python standards
- Use type hints
- Write docstrings for complex functions

### Before Pushing
```bash
pip install -r requirements.txt
pytest  # Ensure tests pass
UVICORN_RELOAD=1 python run.py  # Test locally
```

### Making Changes
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test
3. Commit: `git commit -m "Add feature description"`
4. Push: `git push origin feature/your-feature`
5. Create Pull Request on GitHub

---

## 🎯 Getting Involved

Want to contribute? We'd love your help! 🙌

- **Report bugs** — Found an issue? Open a GitHub issue
- **Suggest features** — Have an idea? Start a discussion
- **Improve docs** — Help us document better
- **Code contributions** — Submit a PR with improvements
- **Test the app** — Use it and share feedback

---

## 📞 Support & Questions

- 💬 **Questions?** Check `/api/docs` for API reference
- 🐛 **Found a bug?** Create an issue on GitHub
- 📧 **Contact us** — Reach out to the development team

---

## 📄 License

[Your License Here - MIT, Apache 2.0, etc.]

---

## ✨ Join the Karivari Community

Every booking, every listing, every review helps us build a **safer, more connected Uganda**. 

Whether you're an adventurer seeking the perfect 4×4 or an owner looking to monetize your vehicle, **Karivari Uganda is your platform.**

🚀 **[Start exploring now →](https://webapp-01os.onrender.com/)**

---

**Version:** 1.0.0  
**Last Updated:** June 2026  
**Status:** 🟢 Active & Maintained

