# Karivari Uganda — Full-Stack Web App
## Agent Build Plan

**Stack:** HTML · CSS · Vanilla JavaScript · FastAPI · SQLite
**Roles:** Tourist · Car Owner · Driver · Admin
**Scope:** v1 production-ready booking platform

---

## 0. How to Use This Plan

This plan is structured for an autonomous coding agent (Claude Code, Cursor, etc.). Work through phases sequentially. Do not skip phases — later phases depend on earlier scaffolding. After each phase, run the verification step before moving on.

**Discipline rules for the agent:**
- One feature per commit. Never bundle unrelated changes.
- Write the API endpoint and its tests before writing the frontend that consumes it.
- If a requirement is ambiguous, write the assumption as a comment in code and continue. Do not stall asking questions.
- Use SQLite WAL mode and parameterised queries everywhere. Never string-concatenate SQL.
- Hash passwords with bcrypt. Never store plaintext, never log tokens.

---

## 1. System Overview

Karivari is a marketplace connecting verified Ugandan 4×4 vehicles and drivers with international tourists. The app supports four roles, each with a distinct dashboard and capabilities. The backend exposes a REST API; the frontend is a multi-page vanilla JS app that calls it.

### 1.1 User Roles & Core Capabilities

| Role | Primary Actions |
|------|----------------|
| **Tourist** | Sign up, **complete KYC (passport or national ID + selfie)**, browse vehicles, filter by trip type, book multi-day trips, pay, message driver, review trip |
| **Car Owner** | Submit vehicle for verification, manage fleet availability, view bookings & earnings, get notified of dispatch |
| **Driver** | Onboarding & training modules, accept/decline trip assignments, view trip schedule, communicate with tourists, see ratings |
| **Admin** | Verify owners/drivers/vehicles, resolve disputes, run KPI dashboard, manage partners, override bookings |

### 1.2 Architecture (text diagram)

```
┌─────────────────────┐       ┌──────────────────────┐       ┌─────────────┐
│  Browser (vanilla   │  HTTP │  FastAPI backend     │  SQL  │  SQLite     │
│  JS, HTML, CSS)     │ <───> │  (uvicorn + routers) │ <───> │  (WAL mode) │
│                     │       │                      │       │             │
│  - public site      │       │  - auth (JWT)        │       │  - tables   │
│  - tourist app      │       │  - role guards       │       │  - indexes  │
│  - owner dashboard  │       │  - business logic    │       │  - triggers │
│  - driver dashboard │       │  - payment webhook   │       │             │
│  - admin console    │       │  - email worker      │       │             │
└─────────────────────┘       └──────────────────────┘       └─────────────┘
                                       │
                                       ├──> SendGrid / SMTP (emails)
                                       ├──> Stripe / Flutterwave (payments)
                                       └──> Onfido / Persona / Veriff (KYC)
```

### 1.3 Deliverable at end of v1

A single repository deployable to one VM, containing: backend API, frontend static files served by FastAPI, SQLite database, seed data, README, and a `docker-compose.yml` for local dev.

---

## 2. Repository Layout

```
karivari/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entrypoint
│   │   ├── config.py                # env vars, settings
│   │   ├── database.py              # SQLite connection, WAL setup
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── schemas.py               # Pydantic request/response schemas
│   │   ├── security.py              # password hash, JWT, role guards
│   │   ├── deps.py                  # FastAPI dependencies (current_user, db)
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── vehicles.py
│   │   │   ├── bookings.py
│   │   │   ├── drivers.py
│   │   │   ├── reviews.py
│   │   │   ├── payments.py
│   │   │   ├── messages.py
│   │   │   ├── admin.py
│   │   │   └── analytics.py
│   │   ├── services/
│   │   │   ├── email.py             # async email sender
│   │   │   ├── pricing.py           # daily-rate + insurance calc
│   │   │   ├── payments.py          # Stripe/Flutterwave wrapper
│   │   │   └── notifications.py     # in-app + email orchestrator
│   │   └── seed.py                  # demo data generator
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_bookings.py
│   │   ├── test_admin.py
│   │   └── conftest.py
│   ├── alembic/                     # migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── public/
│   │   ├── index.html               # landing
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── vehicles.html            # browse
│   │   ├── vehicle.html             # detail page
│   │   ├── checkout.html
│   │   ├── tourist/
│   │   │   ├── dashboard.html
│   │   │   └── bookings.html
│   │   ├── owner/
│   │   │   ├── dashboard.html
│   │   │   ├── vehicles.html
│   │   │   └── earnings.html
│   │   ├── driver/
│   │   │   ├── dashboard.html
│   │   │   ├── training.html
│   │   │   └── schedule.html
│   │   └── admin/
│   │       ├── dashboard.html
│   │       ├── verifications.html
│   │       ├── kpis.html
│   │       └── disputes.html
│   ├── css/
│   │   ├── base.css                 # reset + typography + tokens
│   │   ├── components.css           # buttons, cards, forms
│   │   └── layout.css               # grid, dashboards
│   └── js/
│       ├── api.js                   # fetch wrapper, auth header
│       ├── auth.js                  # login/signup/logout
│       ├── router.js                # role-based redirect
│       ├── components/              # reusable render functions
│       └── pages/                   # one file per page
├── docker-compose.yml
├── Dockerfile
├── README.md
└── .gitignore
```

---

## 3. Data Model (SQLite Schema)

Build these tables in order. Every table has `created_at` and `updated_at` (TEXT, ISO 8601). Use foreign keys with `ON DELETE` policies as noted.

### 3.1 Core tables

**users** — single table for all roles
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
email TEXT UNIQUE NOT NULL
password_hash TEXT NOT NULL
full_name TEXT NOT NULL
phone TEXT
role TEXT NOT NULL CHECK(role IN ('tourist','owner','driver','admin'))
country TEXT                        -- ISO 3166-1 alpha-2
preferred_language TEXT DEFAULT 'en'
is_verified INTEGER DEFAULT 0       -- 0/1
is_active INTEGER DEFAULT 1
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
```

**vehicles**
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
make TEXT NOT NULL                  -- e.g., Toyota
model TEXT NOT NULL                 -- e.g., Land Cruiser
year INTEGER NOT NULL
license_plate TEXT UNIQUE NOT NULL
seats INTEGER NOT NULL
luggage_capacity INTEGER NOT NULL   -- bags
has_pop_top INTEGER DEFAULT 0       -- for photography
has_ac INTEGER DEFAULT 1
daily_rate_usd REAL NOT NULL
status TEXT NOT NULL CHECK(status IN ('pending','verified','rejected','suspended'))
verification_notes TEXT
location_base TEXT                  -- Kampala, Entebbe, etc.
created_at TEXT, updated_at TEXT
```

**vehicle_photos**
```sql
id INTEGER PRIMARY KEY
vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE CASCADE
file_path TEXT NOT NULL
is_primary INTEGER DEFAULT 0
```

**driver_profiles** (1-to-1 with users where role='driver')
```sql
user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE
license_number TEXT UNIQUE NOT NULL
license_expiry TEXT NOT NULL
years_experience INTEGER NOT NULL
languages TEXT                      -- JSON: ["English","Swahili","German"]
specialties TEXT                    -- JSON: ["photography","wildlife"]
training_completed INTEGER DEFAULT 0
training_completed_at TEXT
rating_avg REAL DEFAULT 0
rating_count INTEGER DEFAULT 0
status TEXT CHECK(status IN ('pending','verified','rejected','suspended'))
```

**bookings**
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
booking_code TEXT UNIQUE NOT NULL    -- e.g., KRV-2026-00123
tourist_id INTEGER NOT NULL REFERENCES users(id)
vehicle_id INTEGER NOT NULL REFERENCES vehicles(id)
driver_id INTEGER REFERENCES users(id)
trip_type TEXT CHECK(trip_type IN ('photography','wildlife','luxury','general'))
start_date TEXT NOT NULL
end_date TEXT NOT NULL
pickup_location TEXT NOT NULL
dropoff_location TEXT NOT NULL
itinerary TEXT                       -- free text
num_passengers INTEGER NOT NULL
daily_rate_usd REAL NOT NULL         -- snapshot at booking time
total_days INTEGER NOT NULL
subtotal_usd REAL NOT NULL
insurance_usd REAL NOT NULL
total_usd REAL NOT NULL
status TEXT NOT NULL CHECK(status IN
  ('pending_payment','confirmed','in_progress','completed','cancelled','disputed'))
payment_status TEXT CHECK(payment_status IN ('unpaid','paid','refunded','failed'))
cancellation_reason TEXT
created_at TEXT, updated_at TEXT
```

**payments**
```sql
id INTEGER PRIMARY KEY
booking_id INTEGER NOT NULL REFERENCES bookings(id)
provider TEXT CHECK(provider IN ('stripe','flutterwave','manual'))
provider_ref TEXT                    -- external payment ID
amount_usd REAL NOT NULL
currency TEXT DEFAULT 'USD'
status TEXT CHECK(status IN ('initiated','succeeded','failed','refunded'))
raw_payload TEXT                     -- JSON dump of webhook
created_at TEXT
```

**reviews**
```sql
id INTEGER PRIMARY KEY
booking_id INTEGER UNIQUE REFERENCES bookings(id)
tourist_id INTEGER REFERENCES users(id)
vehicle_rating INTEGER CHECK(vehicle_rating BETWEEN 1 AND 5)
driver_rating INTEGER CHECK(driver_rating BETWEEN 1 AND 5)
overall_rating INTEGER CHECK(overall_rating BETWEEN 1 AND 5)
comment TEXT
created_at TEXT
```

**messages** (booking-scoped chat between tourist and driver)
```sql
id INTEGER PRIMARY KEY
booking_id INTEGER REFERENCES bookings(id)
sender_id INTEGER REFERENCES users(id)
body TEXT NOT NULL
is_read INTEGER DEFAULT 0
created_at TEXT
```

**notifications**
```sql
id INTEGER PRIMARY KEY
user_id INTEGER REFERENCES users(id)
type TEXT                            -- 'booking_confirmed', 'verification_complete', etc.
title TEXT NOT NULL
body TEXT NOT NULL
link TEXT                            -- relative URL the notification opens
is_read INTEGER DEFAULT 0
created_at TEXT
```

**verification_documents**
```sql
id INTEGER PRIMARY KEY
user_id INTEGER REFERENCES users(id)
vehicle_id INTEGER REFERENCES vehicles(id)  -- nullable
doc_type TEXT                        -- 'id', 'license', 'registration', 'insurance'
file_path TEXT NOT NULL
status TEXT CHECK(status IN ('pending','approved','rejected'))
reviewed_by INTEGER REFERENCES users(id)
reviewed_at TEXT
created_at TEXT
```

**tourist_kyc** (one row per tourist; tracks identity verification)
```sql
user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE
document_type TEXT CHECK(document_type IN ('passport','national_id'))
document_number_hash TEXT            -- bcrypt/sha256 of doc number; never store plaintext
document_country TEXT                -- ISO 3166-1 alpha-2 of issuing country
document_expiry TEXT                 -- ISO date
full_name_on_doc TEXT                -- as captured by KYC provider
date_of_birth TEXT                   -- ISO date; used for age >= 18 check
provider TEXT CHECK(provider IN ('onfido','persona','veriff','manual'))
provider_check_id TEXT               -- external KYC reference
provider_status TEXT                 -- raw status from provider
status TEXT NOT NULL CHECK(status IN
  ('not_started','in_progress','approved','rejected','expired','manual_review'))
risk_score REAL                      -- 0.0–1.0 if provider returns one
rejection_reason TEXT
submitted_at TEXT
decided_at TEXT
reviewed_by INTEGER REFERENCES users(id)  -- admin who handled manual_review
attempts INTEGER DEFAULT 0           -- count of submissions; cap at 3
created_at TEXT, updated_at TEXT
```

Notes on `tourist_kyc`:
- One row per tourist, created on first KYC initiation. Row exists with `status='not_started'` until they begin.
- `document_number_hash` is a one-way hash; we never need the raw number after verification, only to detect re-use across accounts (look up by hash).
- A separate uniqueness index on `(document_type, document_number_hash)` prevents the same document being used by two different accounts (fraud signal).
- KYC expires after 24 months — a background job sets `status='expired'` and forces re-verification before the next booking.

**training_modules** (for drivers)
```sql
id INTEGER PRIMARY KEY
title TEXT NOT NULL
description TEXT
content_url TEXT                     -- video / pdf path
order_index INTEGER
is_active INTEGER DEFAULT 1
```

**driver_training_progress**
```sql
id INTEGER PRIMARY KEY
driver_id INTEGER REFERENCES users(id)
module_id INTEGER REFERENCES training_modules(id)
completed_at TEXT
score INTEGER                        -- optional quiz score
UNIQUE(driver_id, module_id)
```

**audit_log** (admin actions)
```sql
id INTEGER PRIMARY KEY
admin_id INTEGER REFERENCES users(id)
action TEXT                          -- 'verify_vehicle', 'suspend_owner', etc.
target_type TEXT                     -- 'vehicle', 'user', 'booking'
target_id INTEGER
details TEXT                         -- JSON
created_at TEXT
```

### 3.2 Indexes (must create)
```sql
CREATE INDEX idx_bookings_tourist ON bookings(tourist_id, status);
CREATE INDEX idx_bookings_driver ON bookings(driver_id, start_date);
CREATE INDEX idx_bookings_vehicle ON bookings(vehicle_id, start_date, end_date);
CREATE INDEX idx_vehicles_status ON vehicles(status, location_base);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_messages_booking ON messages(booking_id, created_at);
CREATE UNIQUE INDEX idx_kyc_doc_uniqueness
  ON tourist_kyc(document_type, document_number_hash)
  WHERE status = 'approved';                 -- one approved KYC per real document
CREATE INDEX idx_kyc_status ON tourist_kyc(status);
```

### 3.3 Critical invariants
1. **No double-booking.** Enforce in the booking-creation transaction with a SELECT … WHERE overlap check inside a `BEGIN IMMEDIATE` transaction, not just at the application layer.
2. **No booking without KYC.** The booking-creation endpoint must verify `tourist_kyc.status = 'approved'` for the requesting tourist before any other check. Enforce server-side; the client-side check is for UX only.
3. **No duplicate identities.** The unique index above prevents the same passport/national-ID being approved on two accounts. If a hash collision is detected during KYC submission, the row is set to `manual_review` and an admin is alerted (could be a legitimate reissue, could be fraud).

---

## 4. API Surface (FastAPI endpoints)

All endpoints return JSON. All write endpoints require `Authorization: Bearer <jwt>`. JWT carries `user_id` and `role`. Use FastAPI dependencies to enforce role guards.

### 4.1 Auth
```
POST   /api/auth/signup              { email, password, full_name, role, ... }
POST   /api/auth/login               { email, password } -> { access_token, user }
POST   /api/auth/refresh             { refresh_token }
POST   /api/auth/logout
GET    /api/auth/me
POST   /api/auth/forgot-password     { email }
POST   /api/auth/reset-password      { token, new_password }
```

### 4.2 Users
```
GET    /api/users/me
PATCH  /api/users/me
POST   /api/users/me/avatar
GET    /api/users/{id}               (admin only, or self)
```

### 4.3 Tourist KYC
```
GET    /api/kyc/me                   current KYC status for logged-in tourist
POST   /api/kyc/me/initiate          create check; returns provider SDK token + check_id
POST   /api/kyc/me/submit            (only used in 'manual' fallback flow) multipart
POST   /api/kyc/webhook              provider callback, signature-verified, no auth
GET    /api/admin/kyc/manual-review  (admin) list of rows in manual_review
PATCH  /api/admin/kyc/{user_id}/approve   (admin) override approve with reason
PATCH  /api/admin/kyc/{user_id}/reject    (admin) override reject with reason
```

### 4.3 Vehicles (browse + manage)
```
GET    /api/vehicles                 ?location=&trip_type=&min_seats=&from=&to=
GET    /api/vehicles/{id}
POST   /api/vehicles                 (owner) submit new vehicle
PATCH  /api/vehicles/{id}            (owner of vehicle)
DELETE /api/vehicles/{id}            (owner)
POST   /api/vehicles/{id}/photos     multipart upload
GET    /api/vehicles/{id}/availability ?from=&to=
```

### 4.4 Bookings
```
POST   /api/bookings                 (tourist) create pending_payment booking
GET    /api/bookings                 (role-filtered list)
GET    /api/bookings/{id}            (parties + admin)
PATCH  /api/bookings/{id}/cancel
PATCH  /api/bookings/{id}/assign-driver   (admin)
PATCH  /api/bookings/{id}/start            (driver, on trip start)
PATCH  /api/bookings/{id}/complete         (driver, on trip end)
```

### 4.5 Payments
```
POST   /api/payments/initiate        { booking_id } -> { checkout_url }
POST   /api/payments/webhook         (provider callback, no auth — verified by signature)
GET    /api/payments/{booking_id}/status
```

### 4.6 Drivers
```
GET    /api/drivers/me/profile
PATCH  /api/drivers/me/profile
GET    /api/drivers/me/trips         ?status=upcoming|active|past
GET    /api/drivers/me/training
POST   /api/drivers/me/training/{module_id}/complete
PATCH  /api/bookings/{id}/respond    (driver) accept/decline assignment
```

### 4.7 Reviews
```
POST   /api/bookings/{id}/review     (tourist, after completed)
GET    /api/vehicles/{id}/reviews
GET    /api/drivers/{id}/reviews
```

### 4.8 Messages
```
GET    /api/bookings/{id}/messages
POST   /api/bookings/{id}/messages   { body }
PATCH  /api/messages/{id}/read
```

### 4.9 Notifications
```
GET    /api/notifications            ?unread_only=true
PATCH  /api/notifications/{id}/read
POST   /api/notifications/read-all
```

### 4.10 Admin
```
GET    /api/admin/verifications/pending       ?type=owner|driver|vehicle
PATCH  /api/admin/verifications/{id}/approve
PATCH  /api/admin/verifications/{id}/reject   { reason }
GET    /api/admin/users                       ?role=&search=
PATCH  /api/admin/users/{id}/suspend
GET    /api/admin/bookings                    (all bookings, with filters)
PATCH  /api/admin/bookings/{id}/override-status
GET    /api/admin/disputes
PATCH  /api/admin/disputes/{id}/resolve
```

### 4.11 Analytics (admin KPI dashboard)
```
GET    /api/admin/analytics/overview          -> headline KPIs
GET    /api/admin/analytics/bookings          ?from=&to=&group_by=day|week|month
GET    /api/admin/analytics/revenue           ?from=&to=
GET    /api/admin/analytics/fleet-utilisation
GET    /api/admin/analytics/top-routes
GET    /api/admin/analytics/conversion-funnel
GET    /api/admin/analytics/driver-performance
GET    /api/admin/analytics/customer-segments  -> photography/wildlife/luxury split
```

KPIs to compute in the analytics endpoints:
- **Bookings:** total, by status, by trip type, average trip length
- **Revenue:** GMV (gross merchandise value), Karivari margin, refunds
- **Supply:** verified vehicles count, active drivers, fleet utilisation %
- **Quality:** avg vehicle rating, avg driver rating, complaint rate
- **Funnel:** signups → vehicle views → bookings created → bookings paid → completed
- **Partner attribution:** bookings by referral source

---

## 5. Build Phases

Each phase has a goal, tasks, and a verification step. The agent must run verification before moving on.

---

### Phase 1 — Project Scaffolding
**Goal:** Working FastAPI app serving a placeholder homepage.

Tasks:
1. Create the repo layout in Section 2.
2. Set up `requirements.txt`: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `pydantic[email]`, `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`, `httpx`, `pytest`, `pytest-asyncio`.
3. Create `app/main.py` that mounts `frontend/public` at `/` and exposes `/api/health`.
4. Set up `database.py` with SQLite + WAL mode (`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`).
5. Configure CORS to allow the frontend origin in dev.
6. Add a `Dockerfile` and `docker-compose.yml`.
7. Add a basic `README.md` with setup instructions.

Verification: `docker compose up` succeeds; `GET /api/health` returns `{"status":"ok"}`; browser at `/` shows a placeholder.

---

### Phase 2 — Data Model & Migrations
**Goal:** All tables from Section 3 created and seedable.

Tasks:
1. Define SQLAlchemy models for every table in Section 3.
2. Initialise Alembic; generate the initial migration; apply it.
3. Add all indexes from Section 3.2.
4. Build `seed.py` that creates: 1 admin, 3 owners, 5 drivers, 8 vehicles, 5 training modules, 10 tourists, and 6 sample bookings across statuses.
5. Add a CLI command `python -m app.seed` that resets and seeds the DB.

Verification: After seeding, `sqlite3 karivari.db ".tables"` lists all tables, and counts match the seed plan.

---

### Phase 3 — Auth & Roles
**Goal:** Working signup, login, role-guarded endpoints.

Tasks:
1. Implement bcrypt password hashing in `security.py`.
2. JWT issuance with `python-jose`. Access token 30 min, refresh token 14 days. Refresh tokens stored in DB so they can be revoked.
3. Build endpoints in Section 4.1.
4. Build the `current_user` dependency and `require_role(*roles)` factory.
5. Apply role guards to every protected endpoint scaffolded so far (even if just placeholder).
6. Write tests: signup happy path, login, wrong password, expired token, role-guard rejection.

Verification: All Section 4.1 endpoints work via curl. Test suite passes.

---

### Phase 4 — Vehicle Submission & Verification
**Goal:** Owner can submit a vehicle; admin can approve/reject.

Tasks:
1. Implement Section 4.3 endpoints. Vehicles are created with `status='pending'`.
2. Photo upload: store under `uploads/vehicles/{vehicle_id}/` with sanitised filenames and a max size (5 MB per photo, max 8 photos).
3. Implement `/api/admin/verifications/pending?type=vehicle` and the approve/reject endpoints.
4. On approve: set vehicle status, write `audit_log`, send notification + email to owner.
5. On reject: set status, capture reason, notify owner.
6. Tests: owner can only edit own vehicles, non-owner gets 403, admin verification flow end-to-end.

Verification: Manually submit a vehicle as owner; verify it as admin; check notifications fire.

---

### Phase 5 — Driver Onboarding & Training
**Goal:** Drivers complete training before becoming eligible for trips.

Tasks:
1. Build driver profile endpoints (Section 4.6).
2. Implement training module list + completion endpoints.
3. Business rule: a driver cannot be assigned to a booking unless `training_completed = 1` AND `status = 'verified'`. Enforce in the assignment endpoint and surface a clear 422 error.
4. Add the admin endpoints to approve/reject driver verification (license, ID).
5. Driver dashboard data endpoint: counts of upcoming/active/past trips.
6. Tests: training completion sets the flag at the right threshold; unverified driver cannot be assigned.

Verification: Seed driver, complete all training modules via API, verify the flag flips.

---

### Phase 6 — Search & Browse (Tourist)
**Goal:** Tourists can browse and filter vehicles.

Tasks:
1. Implement `GET /api/vehicles` with filters: `location`, `trip_type`, `min_seats`, `from`, `to`, `max_daily_rate`. Only return `status='verified'`.
2. Date filter must exclude vehicles with overlapping `confirmed`/`in_progress` bookings (this is the key query — write a SQL CTE).
3. Implement `GET /api/vehicles/{id}` returning vehicle + photos + owner display name + recent reviews + computed available date ranges.
4. Sort options: `daily_rate_asc`, `daily_rate_desc`, `rating_desc`, `newest`.
5. Paginate: `?page=1&page_size=20`. Return `{items, total, page, pages}`.
6. Tests: filter combinations, overlap query correctness.

Verification: Browse endpoint returns only verified, non-conflicting vehicles for a date range.

---

### Phase 7 — Tourist KYC (identity verification)
**Goal:** Every tourist must complete passport/national-ID verification before they can create a booking.

This phase is a hard gate: the booking endpoint built in the next phase will refuse any request from a tourist whose `tourist_kyc.status != 'approved'`. Browsing remains open to all signed-in tourists so they can see prices and plan, but the "Book" button is disabled until KYC is approved.

**Provider choice:** pick one of Onfido, Persona, or Veriff in config. The integration is wrapped behind `services/kyc.py` so the provider can be swapped without touching routers. v1 ships with one provider; the `manual` fallback flow exists for cases where the provider can't reach the user (e.g. country restrictions, document not supported).

Tasks:
1. Build `services/kyc.py` with a provider-agnostic interface:
   - `create_check(user, doc_type) -> {check_id, sdk_token, redirect_url}`
   - `verify_webhook(payload, signature) -> normalised_result`
   - `fetch_check(check_id) -> normalised_result`
   The normalised result has: `status` (one of `approved`/`rejected`/`manual_review`/`in_progress`), `risk_score`, `document_type`, `document_number`, `document_country`, `document_expiry`, `full_name_on_doc`, `date_of_birth`, raw provider payload.
2. Implement `POST /api/kyc/me/initiate`:
   - Reject if the tourist already has `status='approved'` (no-op success), or has `attempts >= 3` (must contact support).
   - Create or update the `tourist_kyc` row to `in_progress`, increment `attempts`, store `provider_check_id`.
   - Return the SDK token / redirect URL the frontend needs.
3. Implement `POST /api/kyc/webhook`:
   - Verify the provider's signature header. Reject if invalid.
   - Idempotent on `provider_check_id` — replaying must not double-update.
   - Map the provider status to the local `status`:
     - clear pass → `approved`, set `decided_at`, hash and store `document_number`, store the rest of the doc data
     - clear fail → `rejected`, capture reason
     - inconclusive / high risk → `manual_review`, notify admins
   - Run the duplicate-document check: if another user already has `status='approved'` for the same `(document_type, document_number_hash)`, force `manual_review` instead of `approved`.
   - Age check: reject if `date_of_birth` implies the user is under 18.
   - On `approved`: send "Verification complete" email + notification. On `rejected`: send email with reason and "try again" CTA.
4. Implement `GET /api/kyc/me`:
   - Returns `{status, attempts, can_retry, rejection_reason, expires_at}` so the frontend knows what to show.
5. Implement admin endpoints in Section 4.3:
   - `GET /api/admin/kyc/manual-review` — paginated list with provider's reason and document preview link (signed URL, expires in 10 min).
   - `PATCH /api/admin/kyc/{user_id}/approve` and `/reject` — both require a `reason` and both write to `audit_log`.
6. **Booking-endpoint gate** (will be enforced in Phase 8, but stub it now): add `require_kyc_approved` dependency that loads `tourist_kyc` for the current user and raises 403 with body `{"error":"kyc_required","kyc_status":"..."}` if not approved.
7. **Expiry job:** APScheduler task runs daily at 02:00 UTC; sets `status='expired'` for any approved row older than 24 months. Emails the affected user.
8. **Privacy:** raw document images are NOT stored on Karivari's servers. The provider holds them. We only store the hash of the document number, the doc-issuing country, expiry date, and the provider's decision metadata. Document this in the README under "Data we store about tourists."
9. **Manual fallback** (`provider='manual'`): hidden behind a feature flag for v1. When enabled, the user uploads images to `/api/kyc/me/submit`, files land in `uploads/kyc/{user_id}/` with restrictive ACLs, and an admin reviews them in the manual-review queue.
10. Tests:
    - Webhook signature verification (valid passes, tampered fails).
    - Webhook idempotency (replay same payload twice → one state change).
    - Duplicate-document detection forces `manual_review`.
    - Under-18 forces `rejected`.
    - Attempt cap at 3.
    - The booking gate stub raises 403 with the right body when KYC is missing.

Verification: A test tourist completes the provider's sandbox flow end-to-end; the webhook arrives; the row flips to `approved`; the `GET /api/kyc/me` returns the right shape; and calling the (stubbed) booking endpoint with a non-approved tourist returns 403 with `error: "kyc_required"`.

---

### Phase 8 — Booking Creation
**Goal:** Tourist can create a booking; system holds the slot until paid.

Tasks:
1. **KYC gate first.** Apply the `require_kyc_approved` dependency (built in Phase 7) to `POST /api/bookings`. Any tourist whose KYC is not `approved` gets a 403 with `{"error":"kyc_required","kyc_status":"..."}` before any other validation runs.
2. Implement `POST /api/bookings`. Use a `BEGIN IMMEDIATE` transaction, re-check availability, compute pricing via `services/pricing.py` (daily_rate × days + insurance flat fee from config), generate `booking_code`, insert as `pending_payment`. Also snapshot the tourist's KYC'd full name and date of birth onto the booking row (add columns if useful for the driver to verify identity on pickup).
3. Hold rule: pending_payment bookings expire after 30 minutes if not paid. Implement an APScheduler job that runs every minute to expire stale holds.
4. Implement cancellation rules: free cancellation > 7 days before start, 50% fee 7–2 days, no refund < 48h.
5. Implement assign-driver endpoint (admin). Cannot assign an unverified or untrained driver. Cannot assign a driver who has overlapping trips.
6. Driver respond endpoint (accept/decline). On decline, booking returns to `confirmed` with `driver_id = NULL` and an admin notification fires.
7. Implement trip lifecycle: `start` (driver, sets status `in_progress`), `complete` (driver, sets `completed`, triggers review invitation).
8. Tests: KYC gate rejects unverified tourists, double-booking prevention, hold expiry, cancellation fee logic, driver overlap.

Verification: Race-condition test — fire 5 concurrent booking requests for the same dates; only one succeeds. Separate test: a tourist without KYC gets 403 on every shape of valid booking payload.

---

### Phase 9 — Payments
**Goal:** Tourist can pay; webhook updates booking status.

Tasks:
1. Pick provider in config: `stripe` for cards, `flutterwave` for African mobile money. Build `services/payments.py` with a common interface (`create_checkout(booking)`, `verify_webhook(payload, signature)`).
2. Implement `POST /api/payments/initiate` — creates a checkout session, stores `provider_ref`, returns the redirect URL.
3. Implement `POST /api/payments/webhook` — verifies signature, idempotent on `provider_ref`, updates payment row + booking `payment_status` + `status='confirmed'` on success.
4. On payment success: send confirmation email with booking code, insurance certificate (PDF generation can be deferred), and itinerary.
5. Implement refund flow on cancellation (call provider refund API, mark payment refunded).
6. Tests: webhook signature verification, idempotency (replaying the same webhook doesn't double-update), failed payment leaves booking in `pending_payment`.

Verification: End-to-end booking → pay (test mode) → email received → booking shows `confirmed`.

---

### Phase 10 — Reviews & Ratings
**Goal:** Tourists rate trips; vehicles and drivers accumulate ratings.

Tasks:
1. Implement `POST /api/bookings/{id}/review` (only if status=completed, only by the tourist, only once).
2. On insert, update `driver_profiles.rating_avg/count` and a computed `vehicle.rating_avg/count` (add columns if not present, recalc with a trigger or in the endpoint).
3. Public review endpoints for vehicle and driver pages.
4. Profanity check: a simple word-list filter rejects reviews with banned terms; admin can override.
5. Tests: rating bounds, single review per booking, average recalculation.

Verification: Complete a trip, submit review, verify averages update.

---

### Phase 11 — Messaging (Tourist ↔ Driver)
**Goal:** Booking-scoped chat between tourist and assigned driver.

Tasks:
1. Implement Section 4.8 endpoints. Only the tourist and assigned driver (and admin) can read/post.
2. Soft real-time: long-polling endpoint `GET /api/bookings/{id}/messages?since={iso}` returning new messages. (WebSockets are out of scope for v1.)
3. Each new message creates a notification for the counterparty.
4. Tests: access control, since-cursor correctness.

Verification: Two browser sessions (tourist + driver) can exchange messages within a booking.

---

### Phase 12 — Notifications & Emails
**Goal:** All key events fan out to email + in-app notifications.

Tasks:
1. Build `services/notifications.py` with one function per event: `booking_created`, `booking_paid`, `booking_assigned_driver`, `driver_assigned_to_you`, `verification_approved`, `verification_rejected`, `trip_starting_tomorrow`, `review_request`, `password_reset`.
2. Each event writes a row to `notifications` and queues an email.
3. Email worker: a background task using FastAPI's `BackgroundTasks` or APScheduler that sends queued emails via SMTP/SendGrid.
4. Email templates: stored as Jinja2 templates in `backend/templates/email/`. Plain HTML, brand colors from the deck (forest green / moss / savanna gold).
5. "Trip starting tomorrow" reminder: scheduled daily at 09:00 Africa/Kampala.
6. Tests: notification rows are created; email queue receives the expected payload.

Verification: Trigger each event manually; confirm both notification row and email sent.

---

### Phase 13 — Admin Verification & Dispute Tools
**Goal:** Admin can verify, suspend, and resolve disputes.

Tasks:
1. Implement Section 4.10 endpoints.
2. Every admin write logs to `audit_log`.
3. Dispute flow: tourist or owner can flag a completed booking → status `disputed` → admin views, gathers info, resolves with refund / partial refund / no action.
4. User suspension: setting `is_active=0` immediately invalidates tokens (check in `current_user` dependency).
5. Tests: audit log entries are written; suspended user gets 401.

Verification: End-to-end dispute: tourist flags, admin reviews, admin issues partial refund.

---

### Phase 14 — Analytics & KPI Dashboard
**Goal:** Admin sees real numbers, not placeholders.

Tasks:
1. Implement Section 4.11 endpoints. Each returns JSON shaped for the chart that consumes it.
2. **Overview** returns: `total_bookings`, `bookings_this_month`, `gmv_usd`, `margin_usd`, `verified_vehicles`, `active_drivers`, `avg_rating`, `nps_proxy` (% of 5-star reviews), `kyc_pass_rate` (approved / total submitted), `kyc_manual_review_open`.
3. **Bookings over time:** group by day/week/month using SQL date functions.
4. **Fleet utilisation:** (booked vehicle-days in period) / (verified vehicles × days in period).
5. **Conversion funnel:** signups → KYC started → KYC approved → first vehicle view (track in a lightweight `events` table) → booking created → paid → completed. Surface the KYC drop-off as its own metric since it's the biggest pre-booking filter.
6. **Customer segments:** count and revenue split by `trip_type`. Also a breakdown of verified tourists by `document_country` to validate the "Germany-first" thesis.
7. **Driver performance:** trips, average rating, decline rate, on-time start rate.
8. Cache expensive queries for 5 minutes in-process.
9. Tests: query correctness on a controlled seed dataset.

Verification: Each KPI matches a hand-computed value from the seed data.

---

### Phase 15 — Frontend Foundation
**Goal:** Shared CSS, JS, and routing in place.

Tasks:
1. Build `css/base.css` with design tokens (forest green `#2C5F2D`, moss `#97BC62`, savanna gold `#D4A574`, cream `#F5F1E8`, ink `#1A2E1F`).
2. `components.css`: buttons (primary/secondary/danger), inputs, cards, badges, tabs, modal, toast.
3. `layout.css`: top nav, sidebar (for dashboards), responsive grid (mobile-first, breakpoint at 768px).
4. `js/api.js`: `apiGet/Post/Patch/Delete` with automatic JWT header, 401 → redirect to login, error toast on failure.
5. `js/auth.js`: token storage in `localStorage` (with the trade-offs noted), `getCurrentUser()` from `/api/auth/me` on page load.
6. `js/router.js`: on every dashboard page, check role and redirect if mismatched.
7. Build the public landing page (use content from the business plan: hero, 3 segments, 3-step "how it works", footer).

Verification: Visiting any role's dashboard URL while logged out redirects to login; with wrong role, redirects to the right dashboard.

---

### Phase 16 — Tourist Frontend
**Goal:** A tourist can sign up, complete KYC, browse, book, pay, view bookings, and review.

Pages: `signup.html`, `login.html`, `tourist/kyc.html`, `vehicles.html`, `vehicle.html`, `checkout.html`, `tourist/dashboard.html`, `tourist/bookings.html`.

Tasks:
1. **Signup/Login:** forms with client-side validation, friendly error display.
2. **KYC page (`tourist/kyc.html`):** loads `GET /api/kyc/me`, then renders one of four states:
   - `not_started` → explainer ("We need to verify your identity before your first booking"), "Start verification" CTA that calls `POST /api/kyc/me/initiate` and launches the provider's SDK / hosted flow.
   - `in_progress` → "We're reviewing your documents — this usually takes a few minutes" with auto-refresh every 30s.
   - `approved` → green check, "You're verified" with the issuing country and expiry.
   - `rejected` → reason text and a "Try again" button (disabled if `attempts >= 3`, replaced with a "Contact support" link).
   - `manual_review` → "Our team is taking a closer look" — no action available.
   - `expired` → "Your verification has expired — please re-verify" CTA.
3. **Routing rule:** the post-login redirect for a tourist checks KYC status. If not `approved`, redirect to `/tourist/kyc.html`. Browsing still works without KYC, but the "Book" button on vehicle detail is disabled with a tooltip "Complete identity verification to book" and links to the KYC page.
4. **Browse:** filter sidebar (location, dates, trip_type, seats, price range), card grid, pagination, sort dropdown.
5. **Vehicle detail:** photo carousel, specs, reviews, "Book this vehicle" CTA opening a date-picker modal that calls availability check before letting the user proceed. The CTA is gated on KYC status as in (3).
6. **Checkout:** read-only summary (vehicle, dates, days, daily rate, insurance, total), pay button → redirect to provider checkout.
7. **Dashboard:** KYC status banner at top (only if not `approved`), upcoming trip card, active booking (with driver contact + message link), past trips list.
8. **Bookings list:** filter by status, action buttons (cancel where allowed, leave review where completed).
9. **Review modal:** stars for vehicle, driver, overall, plus free-text.

Verification: A new visitor signs up, lands on the KYC page, completes the provider's sandbox flow, is redirected to browse with the "Book" button enabled, then completes a booking end-to-end.

---

### Phase 17 — Owner Frontend
**Goal:** An owner can submit vehicles, see bookings against them, and view earnings.

Pages: `owner/dashboard.html`, `owner/vehicles.html`, `owner/earnings.html`.

Tasks:
1. **Dashboard:** counts (verified vehicles, pending verification, active bookings, this-month earnings), upcoming dispatches list.
2. **Vehicles page:** list of own vehicles with status badges, "Add vehicle" wizard (specs → photos → documents → submit), edit pending vehicles, withdraw verified vehicles.
3. **Earnings page:** table of completed bookings with payout amount (after commission), chart of monthly earnings, downloadable CSV.
4. Notification center icon in nav with unread badge.

Verification: Owner adds a vehicle, sees it in "pending"; after admin verifies, it becomes bookable; a tourist booking it appears in the owner's dispatches.

---

### Phase 18 — Driver Frontend
**Goal:** A driver can complete training, see schedule, accept trips, and chat.

Pages: `driver/dashboard.html`, `driver/training.html`, `driver/schedule.html`.

Tasks:
1. **Onboarding gate:** if `training_completed=0`, the dashboard locks behind a training-completion call-to-action.
2. **Training page:** list of modules, status badges, "Mark as complete" button (with a confirmation modal; quiz scoring is optional).
3. **Schedule page:** calendar/list view of assigned trips, accept/decline buttons for new assignments, "Start trip" / "Complete trip" buttons gated by date.
4. **Trip detail:** tourist contact, itinerary, message thread, pickup location with map link.
5. **Ratings:** display avg rating and recent reviews.

Verification: New driver lands on locked dashboard, completes training, gets unlocked; admin assigns a trip; driver sees it and can accept and run the lifecycle.

---

### Phase 19 — Admin Frontend
**Goal:** Admin can do everything in Sections 4.10 and 4.11 through the UI.

Pages: `admin/dashboard.html`, `admin/verifications.html`, `admin/kpis.html`, `admin/disputes.html`.

Tasks:
1. **Dashboard:** headline KPIs (six big-number cards), today's queue (pending verifications, open disputes, bookings awaiting driver assignment, tourist KYC manual reviews).
2. **Verifications:** tabs for Owners / Drivers / Vehicles / **Tourist KYC**, each a list with document previews, approve/reject buttons with reason capture. The Tourist KYC tab loads from `/api/admin/kyc/manual-review`; clicking a row shows the provider's reason, risk score, and the cause of manual escalation (e.g., "duplicate document hash matched user #143"). Approve/reject calls the admin endpoints in Section 4.3.
3. **KPI page:** charts using Chart.js (CDN). Bookings over time (line), revenue by trip type (stacked bar), fleet utilisation (gauge), conversion funnel (funnel/horizontal bars), driver performance (table sortable by rating/trips). Funnel includes a KYC step: signups → KYC started → KYC approved → first booking.
4. **Disputes:** list, detail view with full conversation thread, refund actions.
5. **Users management:** search, filter by role, suspend/unsuspend. Tourist rows show their KYC status badge.

Verification: Open KPI page; numbers match the API responses; every admin action writes to `audit_log` and reflects on the UI. Manual-review queue surfaces escalated KYC cases.

---

### Phase 20 — Hardening
**Goal:** The app is safe to run in production.

Tasks:
1. **Rate limiting:** on login (5/min/IP), signup (3/min/IP), password reset (3/hour/email). Use `slowapi`.
2. **Input validation:** every Pydantic schema has length/format constraints; reject unexpected fields with `extra='forbid'`.
3. **File upload safety:** content-type sniff, max size enforcement, randomise filenames, never trust the original name, store outside the app dir.
4. **Secrets:** all config from env vars; `.env.example` documents every var; no defaults that work in prod.
5. **Logging:** structured JSON logs, never log PII or tokens, log every admin action.
6. **Backups:** a nightly cron that copies `karivari.db` to `backups/karivari-{YYYY-MM-DD}.db`, keeps 14 days.
7. **HTTPS:** Caddy/Traefik reverse proxy in docker-compose handles TLS via Let's Encrypt.
8. **Database:** confirm WAL is on; run `PRAGMA optimize` weekly via cron.
9. **CSRF:** since auth is JWT in `Authorization` header (not cookies), CSRF is mitigated; document this choice in the README.
10. **Security headers:** add `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`, `Content-Security-Policy` with explicit allowlist.

Verification: Run `bandit` on the backend; run `npm audit` if any JS deps; run a basic ZAP baseline scan; all critical/high issues resolved.

---

### Phase 21 — Testing, Docs, Launch Prep
**Goal:** Ship-ready.

Tasks:
1. **Test coverage target:** 70%+ on backend. Critical paths (booking creation, payment webhook, role guards) must be at 100%.
2. **Integration tests:** spin up the app with the seed DB and run scripted user journeys with `httpx`.
3. **README:** local dev setup, prod deploy, env var reference, common operations (reset DB, run seed, take backup).
4. **API docs:** FastAPI auto-generates `/docs`; review every endpoint description, tag, and example.
5. **User docs:** short markdown guides for each role under `docs/`.
6. **Smoke test script:** `scripts/smoke.sh` exercises the critical paths end-to-end against a deployed instance.

Verification: Smoke test passes against a fresh deploy in under 5 minutes.

---

## 6. Cross-Cutting Concerns (apply throughout)

- **Time zones:** store every timestamp in UTC (ISO 8601 with `Z`); convert to Africa/Kampala (UTC+3) for display.
- **Currencies:** tourist-facing prices in USD; admin can also see UGX equivalents via a daily-fetched FX rate (out of scope to integrate live; hardcode a config value for v1).
- **Money math:** never use floats for accounting beyond display; if a payment ledger is needed, store amounts as integer cents.
- **Idempotency keys:** required on POST `/api/bookings` and `/api/payments/initiate`; client supplies a UUID header, server rejects duplicates.
- **Pagination:** every list endpoint paginates; default page_size 20, max 100.
- **i18n:** copy lives in `frontend/js/i18n/{en,de}.json`; the German bundle is a stub for v1 but the structure is wired in.
- **Accessibility:** every form has labels, focus states are visible, color contrast meets WCAG AA.

---

## 7. Out of Scope for v1 (explicitly deferred)

These are deliberately deferred so v1 actually ships:

- Mobile apps (web is responsive; native apps later).
- Real-time WebSockets (long-polling is enough for v1).
- Multi-currency checkout (USD only for now).
- Loyalty / referral codes.
- Partner portal (Reisebüros, Booking.com integration) — v1 captures the demand they send via the standard tourist flow.
- Advanced fraud detection.
- Driver dispatch optimisation algorithms (admin assigns manually).
- PDF generation of insurance certificates (link to an external static template for v1).
- Public API for third parties.

---

## 8. Definition of Done (v1)

The app is done when:

1. All 21 phases verified.
2. A real tourist can sign up, complete KYC (passport or national ID), book a real (seeded) vehicle, pay in test mode, receive emails, and complete the trip lifecycle including review.
3. An owner can submit, get verified, and see bookings.
4. A driver can complete training, be assigned, run a trip, and receive a rating.
5. An admin can verify owners/drivers/vehicles, review escalated tourist KYC cases, manage users, resolve disputes, and see live KPIs.
6. A tourist without approved KYC cannot create a booking under any code path (verified by automated test).
7. The smoke test script passes against a freshly deployed instance.
8. The README lets a new developer get the app running locally in under 10 minutes.

---

## 9. Suggested Build Order Summary

```
Week 1: Phases 1–3   (scaffolding, data, auth)
Week 2: Phases 4–7   (vehicle verification, driver, search, tourist KYC)
Week 3: Phases 8–10  (booking, payments, reviews)
Week 4: Phases 11–14 (messaging, notifications, admin tools, analytics API)
Week 5: Phases 15–18 (frontend foundation + tourist + owner + driver UIs)
Week 6: Phases 19–21 (admin UI, hardening, launch prep)
```

Adjust based on agent throughput. The phase boundaries are designed so the app is testable end-to-end as early as Phase 9 (the booking + payment loop with KYC gating).

---

*End of plan.*
