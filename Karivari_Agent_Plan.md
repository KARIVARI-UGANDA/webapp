# Karivari Uganda -- Full-Stack Web App
## Agent Build Plan (v2 -- Car Owner Model)

**Stack:** HTML / CSS / Vanilla JavaScript / FastAPI / SQLite
**Roles:** Tourist / Car Owner / Admin
**Scope:** v1 production-ready booking platform -- "with driver" only

---

## 0. How to Use This Plan

This plan is structured for an autonomous coding agent (Claude Code, Cursor, etc.). Work through phases sequentially. Do not skip phases -- later phases depend on earlier scaffolding. After each phase, run the verification step before moving on.

**Key architectural decision (v2):**
The driver IS the vehicle owner. Karivari offers exclusively "with driver" trips -- tourists hire a vehicle AND its car owner as a package. There is no self-drive option and no separate driver assignment step. When a booking is confirmed, the car owner is automatically the person responsible for the trip.

**Discipline rules for the agent:**
- One feature per commit. Never bundle unrelated changes.
- Write the API endpoint before writing the frontend that consumes it.
- If a requirement is ambiguous, write the assumption as a comment in code and continue.
- Use SQLite WAL mode and parameterised queries everywhere. Never string-concatenate SQL.
- Hash passwords with bcrypt. Never store plaintext, never log tokens.

---

## 1. System Overview

Karivari is a marketplace connecting verified Ugandan 4x4 car owners with international tourists. Every booking is a fully-staffed experience: the vehicle owner drives their own vehicle. The app supports three roles, each with a distinct dashboard and capabilities. The backend exposes a REST API; the frontend is a multi-page vanilla JS app that calls it.

### 1.1 User Roles & Core Capabilities

| Role | Primary Actions |
|------|----------------|
| **Tourist** | Sign up, complete KYC (passport or national ID + selfie), browse vehicles, filter by trip type, book multi-day trips, pay, message car owner, track trip live, review trip |
| **Car Owner** | Submit vehicle for verification, complete driver onboarding & training, manage fleet availability, accept bookings, run trip lifecycle (start/complete), share live location during trip, view earnings |
| **Admin** | Verify owners/vehicles, review KYC cases, resolve disputes, run KPI dashboard, override bookings |

### 1.2 Architecture

```
+---------------------+       +----------------------+       +-------------+
|  Browser (vanilla   | HTTP  |  FastAPI backend     |  SQL  |  SQLite     |
|  JS, HTML, CSS)     | <---> |  (uvicorn + routers) | <---> |  (WAL mode) |
|                     |       |                      |       |             |
|  - public site      |       |  - auth (JWT)        |       |  - tables   |
|  - tourist app      |       |  - role guards       |       |  - indexes  |
|  - owner dashboard  |       |  - business logic    |       |  - triggers |
|  - admin console    |       |  - payment webhook   |       |             |
|                     |       |  - email worker      |       |             |
+---------------------+       +----------------------+       +-------------+
                                       |
                                       +---> SendGrid / SMTP (emails)
                                       +---> Stripe / Flutterwave (payments)
                                       +---> Onfido / Persona / Veriff (KYC)
```

### 1.3 Deliverable at end of v1

A single repository deployable to one VM: backend API, frontend static files served by FastAPI, SQLite database, seed data, README, and a `docker-compose.yml` for local dev.

---

## 2. Repository Layout

```
karivari/
+-- backend/
|   +-- app/
|   |   +-- __init__.py
|   |   +-- main.py
|   |   +-- config.py
|   |   +-- database.py
|   |   +-- models.py
|   |   +-- schemas.py
|   |   +-- security.py
|   |   +-- deps.py
|   |   +-- routers/
|   |   |   +-- auth.py
|   |   |   +-- users.py
|   |   |   +-- vehicles.py
|   |   |   +-- bookings.py
|   |   |   +-- owners.py          # car owner profile + trips + earnings
|   |   |   +-- tracker.py         # trip tracker endpoints
|   |   |   +-- reviews.py
|   |   |   +-- payments.py
|   |   |   +-- messages.py
|   |   |   +-- admin.py
|   |   |   +-- analytics.py
|   |   +-- services/
|   |   |   +-- email.py
|   |   |   +-- pricing.py
|   |   |   +-- payments.py
|   |   |   +-- notifications.py
|   |   +-- seed.py
|   +-- tests/
|   |   +-- test_auth.py
|   |   +-- test_bookings.py
|   |   +-- test_tracker.py
|   |   +-- test_admin.py
|   |   +-- conftest.py
|   +-- alembic/
|   +-- requirements.txt
|   +-- .env.example
+-- frontend/
|   +-- public/
|   |   +-- index.html
|   |   +-- login.html
|   |   +-- signup.html
|   |   +-- vehicles.html
|   |   +-- vehicle.html
|   |   +-- checkout.html
|   |   +-- tourist/
|   |   |   +-- dashboard.html
|   |   |   +-- bookings.html
|   |   |   +-- tracker.html       # live trip tracking map for tourist
|   |   +-- owner/
|   |   |   +-- dashboard.html
|   |   |   +-- vehicles.html
|   |   |   +-- trips.html         # schedule + active trip controls
|   |   |   +-- earnings.html
|   |   +-- admin/
|   |       +-- dashboard.html
|   |       +-- verifications.html
|   |       +-- kpis.html
|   |       +-- disputes.html
|   +-- css/
|   |   +-- base.css
|   |   +-- components.css
|   |   +-- layout.css
|   +-- js/
|       +-- api.js
|       +-- auth.js
|       +-- router.js
|       +-- components/
|       +-- pages/
+-- docker-compose.yml
+-- Dockerfile
+-- README.md
+-- .gitignore
```

---

## 3. Data Model (SQLite Schema)

Every table has `created_at` and `updated_at` (TEXT, ISO 8601).

### 3.1 Core tables

**users** -- single table for all roles
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
email TEXT UNIQUE NOT NULL
password_hash TEXT NOT NULL
full_name TEXT NOT NULL
phone TEXT
role TEXT NOT NULL CHECK(role IN ('tourist','owner','admin'))
country TEXT
preferred_language TEXT DEFAULT 'en'
is_verified INTEGER DEFAULT 0
is_active INTEGER DEFAULT 1
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
```

**vehicles**
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
make TEXT NOT NULL
model TEXT NOT NULL
year INTEGER NOT NULL
license_plate TEXT UNIQUE NOT NULL
seats INTEGER NOT NULL
luggage_capacity INTEGER NOT NULL
has_pop_top INTEGER DEFAULT 0
has_ac INTEGER DEFAULT 1
daily_rate_usd REAL NOT NULL
status TEXT NOT NULL CHECK(status IN ('pending','verified','rejected','suspended'))
verification_notes TEXT
location_base TEXT
created_at TEXT, updated_at TEXT
```

**vehicle_photos**
```sql
id INTEGER PRIMARY KEY
vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE CASCADE
file_path TEXT NOT NULL
is_primary INTEGER DEFAULT 0
```

**owner_profiles** (1-to-1 with users where role='owner'; covers driving credentials)
```sql
user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE
license_number TEXT UNIQUE NOT NULL
license_expiry TEXT NOT NULL
years_experience INTEGER NOT NULL
languages TEXT              -- JSON: ["English","Swahili","German"]
specialties TEXT            -- JSON: ["photography","wildlife"]
training_completed INTEGER DEFAULT 0
training_completed_at TEXT
bio TEXT
rating_avg REAL DEFAULT 0
rating_count INTEGER DEFAULT 0
status TEXT CHECK(status IN ('pending','verified','rejected','suspended'))
```

**bookings**
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
booking_code TEXT UNIQUE NOT NULL
tourist_id INTEGER NOT NULL REFERENCES users(id)
vehicle_id INTEGER NOT NULL REFERENCES vehicles(id)
-- car owner is derived from vehicle.owner_id; no separate driver assignment needed
trip_type TEXT CHECK(trip_type IN ('photography','wildlife','luxury','general'))
start_date TEXT NOT NULL
end_date TEXT NOT NULL
pickup_location TEXT NOT NULL
dropoff_location TEXT NOT NULL
itinerary TEXT
num_passengers INTEGER NOT NULL
daily_rate_usd REAL NOT NULL
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
provider_ref TEXT
amount_usd REAL NOT NULL
currency TEXT DEFAULT 'USD'
status TEXT CHECK(status IN ('initiated','succeeded','failed','refunded'))
raw_payload TEXT
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

**messages** (booking-scoped chat between tourist and car owner)
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
type TEXT
title TEXT NOT NULL
body TEXT NOT NULL
link TEXT
is_read INTEGER DEFAULT 0
created_at TEXT
```

**verification_documents**
```sql
id INTEGER PRIMARY KEY
user_id INTEGER REFERENCES users(id)
vehicle_id INTEGER REFERENCES vehicles(id)
doc_type TEXT            -- 'id', 'license', 'registration', 'insurance'
file_path TEXT NOT NULL
status TEXT CHECK(status IN ('pending','approved','rejected'))
reviewed_by INTEGER REFERENCES users(id)
reviewed_at TEXT
created_at TEXT
```

**tourist_kyc**
```sql
user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE
document_type TEXT CHECK(document_type IN ('passport','national_id'))
document_number_hash TEXT
document_country TEXT
document_expiry TEXT
full_name_on_doc TEXT
date_of_birth TEXT
provider TEXT CHECK(provider IN ('onfido','persona','veriff','manual'))
provider_check_id TEXT
provider_status TEXT
status TEXT NOT NULL CHECK(status IN
  ('not_started','in_progress','approved','rejected','expired','manual_review'))
risk_score REAL
rejection_reason TEXT
submitted_at TEXT
decided_at TEXT
reviewed_by INTEGER REFERENCES users(id)
attempts INTEGER DEFAULT 0
created_at TEXT, updated_at TEXT
```

**training_modules** (for car owner onboarding)
```sql
id INTEGER PRIMARY KEY
title TEXT NOT NULL
description TEXT
content_url TEXT
order_index INTEGER
is_active INTEGER DEFAULT 1
```

**owner_training_progress**
```sql
id INTEGER PRIMARY KEY
owner_id INTEGER REFERENCES users(id)
module_id INTEGER REFERENCES training_modules(id)
completed_at TEXT
score INTEGER
UNIQUE(owner_id, module_id)
```

**trip_locations** (GPS pings from car owner during a trip)
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE
lat REAL NOT NULL
lng REAL NOT NULL
accuracy REAL                -- GPS accuracy in metres
heading REAL                 -- degrees (0-360), optional
speed REAL                   -- km/h, optional
note TEXT                    -- car owner status note, e.g. "Arrived at Bwindi gate"
recorded_at TEXT NOT NULL    -- ISO 8601 UTC, set by server on receipt
```

**trip_waypoints** (pre-planned itinerary stops, checked off as trip progresses)
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE
name TEXT NOT NULL           -- e.g. "Bwindi Impenetrable Forest"
lat REAL
lng REAL
planned_arrival TEXT         -- ISO date
actual_arrival TEXT          -- set when car owner checks in at this waypoint
order_index INTEGER NOT NULL
```

**audit_log**
```sql
id INTEGER PRIMARY KEY
admin_id INTEGER REFERENCES users(id)
action TEXT
target_type TEXT
target_id INTEGER
details TEXT
created_at TEXT
```

### 3.2 Indexes
```sql
CREATE INDEX idx_bookings_tourist   ON bookings(tourist_id, status);
CREATE INDEX idx_bookings_vehicle   ON bookings(vehicle_id, start_date, end_date);
CREATE INDEX idx_vehicles_status    ON vehicles(status, location_base);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_messages_booking   ON messages(booking_id, created_at);
CREATE INDEX idx_trip_locations_booking ON trip_locations(booking_id, recorded_at);
CREATE UNIQUE INDEX idx_kyc_doc_uniqueness
  ON tourist_kyc(document_type, document_number_hash)
  WHERE status = 'approved';
CREATE INDEX idx_kyc_status ON tourist_kyc(status);
```

### 3.3 Critical invariants
1. **No double-booking.** Enforce inside a `BEGIN IMMEDIATE` transaction with an overlap check.
2. **No booking without KYC.** `tourist_kyc.status = 'approved'` enforced server-side.
3. **No booking a vehicle whose owner is unverified.** `owner_profiles.status = 'verified'` AND `owner_profiles.training_completed = 1` must hold before the vehicle appears in browse results.
4. **Trip tracker only during active trips.** Location pings are rejected if `booking.status != 'in_progress'`.

---

## 4. API Surface (FastAPI endpoints)

All endpoints return JSON. All write endpoints require `Authorization: Bearer <jwt>`.

### 4.1 Auth
```
POST   /api/auth/signup
POST   /api/auth/login          -> { access_token, user }
POST   /api/auth/refresh
POST   /api/auth/logout
GET    /api/auth/me
POST   /api/auth/forgot-password
POST   /api/auth/reset-password
```

### 4.2 Users
```
GET    /api/users/me
PATCH  /api/users/me
POST   /api/users/me/avatar
GET    /api/users/{id}          (admin or self)
```

### 4.3 Tourist KYC
```
GET    /api/kyc/me
POST   /api/kyc/me/initiate
POST   /api/kyc/me/submit       (manual fallback)
POST   /api/kyc/webhook
GET    /api/admin/kyc/manual-review
PATCH  /api/admin/kyc/{user_id}/approve
PATCH  /api/admin/kyc/{user_id}/reject
```

### 4.4 Vehicles
```
GET    /api/vehicles            ?location=&trip_type=&min_seats=&from=&to=
GET    /api/vehicles/{id}
POST   /api/vehicles            (car owner)
PATCH  /api/vehicles/{id}       (car owner of vehicle)
DELETE /api/vehicles/{id}       (car owner)
POST   /api/vehicles/{id}/photos
GET    /api/vehicles/{id}/availability
GET    /api/vehicles/{id}/reviews
```

### 4.5 Bookings
```
POST   /api/bookings            (tourist, KYC-gated)
GET    /api/bookings            (role-filtered list)
GET    /api/bookings/{id}
PATCH  /api/bookings/{id}/cancel
PATCH  /api/bookings/{id}/start     (car owner, sets in_progress)
PATCH  /api/bookings/{id}/complete  (car owner, sets completed -> triggers review invite)
```

Note: there is no assign-driver step. When a booking is confirmed (payment received), the
vehicle's owner is automatically the responsible driver. Availability is managed via the
vehicle calendar, not per-booking acceptance.

### 4.6 Car Owner
```
GET    /api/owners/me/profile
PATCH  /api/owners/me/profile
GET    /api/owners/me/trips          ?status=upcoming|active|past
GET    /api/owners/me/training
POST   /api/owners/me/training/{module_id}/complete
GET    /api/owners/me/earnings       ?from=&to=
```

### 4.7 Trip Tracker
```
POST   /api/bookings/{id}/tracker/ping
       (car owner, during in_progress trip)
       body: { lat, lng, accuracy?, heading?, speed?, note? }

GET    /api/bookings/{id}/tracker/latest
       (tourist or car owner) returns latest location ping + active waypoint

GET    /api/bookings/{id}/tracker/trail
       (tourist or car owner) returns all pings since trip start
       ?since={iso_timestamp}   (for polling -- only pings newer than this)

POST   /api/bookings/{id}/tracker/waypoints/{wp_id}/arrive
       (car owner) marks a pre-planned waypoint as reached

GET    /api/bookings/{id}/tracker/waypoints
       (tourist or car owner) returns full waypoint list with completion status
```

### 4.8 Reviews
```
POST   /api/bookings/{id}/review    (tourist, after completed)
GET    /api/vehicles/{id}/reviews
GET    /api/owners/{id}/reviews
```

### 4.9 Messages
```
GET    /api/bookings/{id}/messages
POST   /api/bookings/{id}/messages   { body }
PATCH  /api/messages/{id}/read
```

### 4.10 Notifications
```
GET    /api/notifications            ?unread_only=true
PATCH  /api/notifications/{id}/read
POST   /api/notifications/read-all
```

### 4.11 Payments
```
POST   /api/payments/initiate        { booking_id } -> { checkout_url }
POST   /api/payments/webhook
GET    /api/payments/{booking_id}/status
```

### 4.12 Admin
```
GET    /api/admin/verifications/pending     ?type=owner|vehicle
PATCH  /api/admin/verifications/{id}/approve
PATCH  /api/admin/verifications/{id}/reject   { reason }
GET    /api/admin/users                       ?role=&search=
PATCH  /api/admin/users/{id}/suspend
GET    /api/admin/bookings
PATCH  /api/admin/bookings/{id}/override-status
GET    /api/admin/disputes
PATCH  /api/admin/disputes/{id}/resolve
```

### 4.13 Analytics (admin KPI dashboard)
```
GET    /api/admin/analytics/overview
GET    /api/admin/analytics/bookings           ?from=&to=&group_by=day|week|month
GET    /api/admin/analytics/revenue            ?from=&to=
GET    /api/admin/analytics/fleet-utilisation
GET    /api/admin/analytics/top-routes
GET    /api/admin/analytics/conversion-funnel
GET    /api/admin/analytics/owner-performance
GET    /api/admin/analytics/customer-segments
```

---

## 5. Build Phases

---

### Phase 1 -- Project Scaffolding
**Goal:** Working FastAPI app serving a placeholder homepage.

Tasks:
1. Create repo layout from Section 2.
2. `requirements.txt`: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `pydantic[email]`, `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`, `httpx`, `pytest`, `pytest-asyncio`.
3. `app/main.py` mounts `frontend/public` at `/` and exposes `GET /api/health`.
4. `database.py` with `PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`.
5. CORS configured for dev origin.
6. `Dockerfile` and `docker-compose.yml`.

Verification: `docker compose up` succeeds; `GET /api/health` returns `{"status":"ok"}`.

---

### Phase 2 -- Data Model & Migrations
**Goal:** All tables created and seedable.

Tasks:
1. SQLAlchemy models for every table in Section 3.
2. Alembic initial migration applied.
3. All indexes from Section 3.2.
4. `seed.py`: 1 admin, 3 car owners (all verified + training complete), 6 vehicles, 5 training modules, 10 tourists, 8 bookings across statuses, sample trip_locations for any `in_progress` booking.

Verification: `sqlite3 karivari.db ".tables"` lists all tables; counts match seed plan.

---

### Phase 3 -- Auth & Roles
**Goal:** Working signup, login, role-guarded endpoints.

Tasks:
1. bcrypt password hashing.
2. JWT (access 30 min, refresh 14 days stored in DB for revocation).
3. Section 4.1 endpoints.
4. `current_user` dependency + `require_role(*roles)` factory.
5. Tests: signup, login, wrong password, expired token, role rejection.

Verification: All auth endpoints work via curl. Test suite passes.

---

### Phase 4 -- Vehicle Submission & Verification
**Goal:** Car owner can submit a vehicle; admin can approve/reject.

Tasks:
1. Section 4.4 endpoints. New vehicles created with `status='pending'`.
2. Photo upload under `uploads/vehicles/{id}/` (max 5 MB, max 8 photos, sanitised names).
3. Admin verify/reject endpoints; on action: write `audit_log`, notify car owner.
4. Browse (`GET /api/vehicles`) only returns vehicles where `status='verified'` AND the owner's `owner_profiles.status='verified'` AND `training_completed=1`.
5. Tests: car owner can only edit own vehicles; non-owner gets 403; unverified owner's vehicles hidden from browse.

Verification: Submit vehicle as car owner -> verify as admin -> vehicle appears in browse.

---

### Phase 5 -- Car Owner Onboarding & Training
**Goal:** Car owner completes driving credentials and training before their vehicles go live.

Tasks:
1. Build `owner_profiles` endpoints (Section 4.6 profile + training).
2. Training modules: list + mark-complete.
3. Business rule: a vehicle is only bookable when `owner_profiles.status='verified'` AND `training_completed=1`. Enforce in both the browse query and the booking-creation endpoint.
4. Admin endpoints to verify/reject car owner (license docs, ID).
5. Tests: untrained / unverified car owner's vehicles excluded from browse; training completion flips the flag.

Verification: Seed car owner, complete all training modules, verify via admin -- vehicles become bookable.

---

### Phase 6 -- Search & Browse (Tourist)
**Goal:** Tourists can browse and filter vehicles.

Tasks:
1. `GET /api/vehicles` with filters: `location`, `trip_type`, `min_seats`, `from`, `to`, `max_daily_rate`. Use a SQL CTE to exclude vehicles with overlapping `confirmed`/`in_progress` bookings.
2. `GET /api/vehicles/{id}` returns vehicle + photos + car owner display info + recent reviews + available date ranges.
3. Sort: `daily_rate_asc`, `daily_rate_desc`, `rating_desc`, `newest`.
4. Pagination: `?page=1&page_size=20`.
5. Tests: filter combinations, date-overlap exclusion.

Verification: Browse returns only verified, available vehicles for a given date range.

---

### Phase 7 -- Tourist KYC
**Goal:** Every tourist must complete identity verification before booking.

Tasks:
1. `services/kyc.py` with provider-agnostic interface.
2. `POST /api/kyc/me/initiate` -- create check, return SDK token.
3. `POST /api/kyc/webhook` -- verify signature, idempotent, map provider status, duplicate-document check, age >= 18 check, notify on decision.
4. `GET /api/kyc/me` -- returns `{status, attempts, can_retry, rejection_reason, expires_at}`.
5. Admin manual-review queue endpoints (Section 4.3).
6. `require_kyc_approved` dependency (used in Phase 8).
7. APScheduler expiry job (daily at 02:00 UTC; marks 24-month-old approved rows as `expired`).
8. Tests: webhook signature, idempotency, duplicate document, under-18, attempt cap.

Verification: Test tourist completes sandbox flow; webhook fires; row flips to `approved`; stubbed booking endpoint returns 403 without it.

---

### Phase 8 -- Booking Creation & Lifecycle
**Goal:** Tourist can create a booking; car owner runs the trip.

Tasks:
1. **KYC gate.** Apply `require_kyc_approved` to `POST /api/bookings`.
2. `POST /api/bookings` in a `BEGIN IMMEDIATE` transaction: re-check availability, compute pricing (`services/pricing.py`), generate `booking_code`, insert as `pending_payment`. 30-minute hold expiry via APScheduler.
3. On payment confirmation (Phase 9): status -> `confirmed`. Car owner receives a notification.
4. Cancellation rules: free > 7 days, 50% fee at 7-2 days, no refund < 48h.
5. `PATCH /api/bookings/{id}/start` (car owner only; requires `status='confirmed'`): sets `status='in_progress'`.
6. `PATCH /api/bookings/{id}/complete` (car owner only; requires `status='in_progress'`): sets `status='completed'`, triggers review invitation to tourist.
7. Tests: KYC gate, double-booking prevention, hold expiry, cancellation fee logic.

Verification: Race-condition test -- 5 concurrent booking requests for the same dates; only one succeeds.

---

### Phase 9 -- Payments
**Goal:** Tourist pays; webhook updates booking status.

Tasks:
1. `services/payments.py`: Stripe (cards) + Flutterwave (mobile money), common interface.
2. `POST /api/payments/initiate` -> checkout session -> redirect URL.
3. `POST /api/payments/webhook` -- verifies signature, idempotent, sets `payment_status='paid'` and `booking.status='confirmed'`.
4. On payment success: confirmation email with booking code and itinerary.
5. Refund flow on cancellation.
6. Tests: webhook signature, idempotency, failed payment leaves `pending_payment`.

Verification: Booking -> pay (test mode) -> email received -> booking shows `confirmed`.

---

### Phase 10 -- Trip Tracker
**Goal:** Tourist can follow the trip on a live map; car owner pings location from their phone/browser.

This is the key differentiating feature of Karivari. The tracker uses the browser Geolocation API on the car owner's side and polling on the tourist's side (no WebSockets in v1).

Tasks:
1. Implement all tracker endpoints from Section 4.7:
   - `POST .../tracker/ping`: validate `status='in_progress'`, insert row into `trip_locations`. Return `{id, recorded_at}`.
   - `GET .../tracker/latest`: return the most recent `trip_locations` row + nearest incomplete waypoint.
   - `GET .../tracker/trail?since=`: return all pings newer than `since`. Max 200 points per response.
   - `POST .../tracker/waypoints/{wp_id}/arrive`: sets `actual_arrival = NOW()` on the waypoint.
   - `GET .../tracker/waypoints`: full waypoint list with completion status.
2. Access control: only the booking's tourist and the vehicle's car owner can access tracker endpoints. Admin can read all.
3. Waypoints are created from the booking's `itinerary` field when the booking is confirmed, or added manually by the car owner via the dashboard.
4. Pings are rejected with 409 once `status` is no longer `in_progress`.
5. Privacy: trip trail deleted 90 days after `completed_at` by a weekly APScheduler job.
6. Tests:
   - Ping rejected when booking is not `in_progress`.
   - Tourist cannot ping (only car owner can).
   - Trail `since` filter correctness.
   - Waypoint arrive is idempotent.

Verification: Seed an `in_progress` booking; post 3 pings as car owner; `GET /trail` returns all 3; `GET /latest` returns the most recent.

---

### Phase 11 -- Reviews & Ratings
**Goal:** Tourists rate trips; vehicles and car owners accumulate ratings.

Tasks:
1. `POST /api/bookings/{id}/review` (only if `status=completed`, only by tourist, only once).
2. On insert: update `owner_profiles.rating_avg/count` and `vehicles.rating_avg/count`.
3. Public review endpoints for vehicle and car owner pages.
4. Profanity filter (word-list; admin can override).
5. Tests: rating bounds, single review per booking, average recalculation.

Verification: Complete a trip, submit review, verify averages update on both vehicle and car owner profile.

---

### Phase 12 -- Messaging (Tourist <-> Car Owner)
**Goal:** Booking-scoped chat between tourist and car owner.

Tasks:
1. Section 4.9 endpoints. Only the tourist and the vehicle's car owner (and admin) can read/post.
2. Long-polling: `GET /api/bookings/{id}/messages?since={iso}` returns new messages.
3. Each new message creates a notification for the counterparty.
4. Tests: access control, since-cursor correctness.

Verification: Two browser sessions (tourist + car owner) can exchange messages.

---

### Phase 13 -- Notifications & Emails
**Goal:** All key events fan out to email + in-app notifications.

Events: `booking_created`, `booking_paid`, `booking_confirmed_owner`, `trip_starting_tomorrow`, `trip_started`, `trip_completed`, `review_request`, `verification_approved`, `verification_rejected`, `password_reset`, `waypoint_reached`.

Tasks:
1. `services/notifications.py` with one function per event.
2. Each writes a `notifications` row and queues an email.
3. Email worker via APScheduler; Jinja2 HTML templates with brand colors.
4. "Trip starting tomorrow" reminder at 09:00 Africa/Kampala.
5. Tests: notification rows created; email queue populated.

Verification: Trigger each event manually; confirm notification row and email sent.

---

### Phase 14 -- Admin Verification & Dispute Tools
**Goal:** Admin can verify, suspend, and resolve disputes.

Tasks:
1. Section 4.12 endpoints. Every admin write logs to `audit_log`.
2. Dispute flow: tourist or car owner flags completed booking -> `disputed` -> admin resolves (refund / partial / none).
3. Suspension: `is_active=0` immediately invalidates tokens.
4. Tests: audit log entries; suspended user gets 401.

Verification: End-to-end dispute: tourist flags -> admin issues partial refund.

---

### Phase 15 -- Analytics & KPI Dashboard
**Goal:** Admin sees real numbers.

Tasks:
1. Section 4.13 endpoints, each returning JSON shaped for the consuming chart.
2. **Overview KPIs:** `total_bookings`, `bookings_this_month`, `gmv_usd`, `margin_usd`, `verified_vehicles`, `active_owners`, `avg_rating`, `nps_proxy`, `kyc_pass_rate`, `kyc_manual_review_open`.
3. **Owner performance:** trips completed, avg rating, on-time start rate, earnings.
4. **Tracker utilisation:** % of `in_progress` trips with at least one ping (measures feature adoption).
5. Cache expensive queries 5 minutes in-process.
6. Tests: query correctness against controlled seed data.

Verification: Each KPI matches a hand-computed value from seed data.

---

### Phase 16 -- Frontend Foundation
**Goal:** Shared CSS, JS, and routing in place.

Tasks:
1. Design tokens: forest green `#2C5F2D`, moss `#97BC62`, savanna gold `#D4A574`, cream `#F5F1E8`, ink `#1A2E1F`.
2. `components.css`: buttons, inputs, cards, badges, tabs, modal, toast.
3. `layout.css`: top nav, sidebar (dashboards), responsive grid.
4. `js/api.js`: fetch wrapper with JWT header, 401 -> redirect, error toast.
5. `js/auth.js`: token storage, `getCurrentUser()`.
6. `js/router.js`: role check + redirect on every dashboard page.
7. Public landing page.

Verification: Dashboard URL while logged out -> redirects to login; wrong role -> redirects to correct dashboard.

---

### Phase 17 -- Tourist Frontend
**Goal:** Tourist can sign up, KYC, browse, book, pay, track trip live, and review.

Pages: `signup.html`, `login.html`, `tourist/kyc.html`, `vehicles.html`, `vehicle.html`, `checkout.html`, `tourist/dashboard.html`, `tourist/bookings.html`, `tourist/tracker.html`.

Tasks:
1. Signup / Login with client-side validation.
2. KYC page: 6 states (not_started, in_progress, approved, rejected, manual_review, expired).
3. Browse with filters; date-range picker calling availability endpoint before checkout.
4. Checkout: read-only summary + pay button.
5. Dashboard: KYC status banner (if not approved), upcoming trip card, active booking with "Track live" CTA.
6. **Trip Tracker page (`tourist/tracker.html`):**
   - Accessible only when booking `status='in_progress'`.
   - Embeds a Leaflet.js map (CDN), centred on Uganda on load.
   - Polls `GET .../tracker/latest` every 15 seconds; plots a marker for the car owner's current position.
   - Polls `GET .../tracker/trail?since=` every 15 seconds; draws a polyline of the route travelled.
   - Waypoints panel: list of stops with green check if `actual_arrival` is set.
   - Latest note from car owner displayed below the map ("Last update: Arrived at Bwindi gate -- 3 min ago").
   - Polling stops automatically when booking is completed.
7. Bookings list: filter by status; cancel (where allowed); leave review (completed trips).
8. Review modal: stars for vehicle, car owner, overall + comment.

Verification: Active booking -> tourist navigates to tracker -> location pings plotted on map in near-real time.

---

### Phase 18 -- Car Owner Frontend
**Goal:** Car owner can manage fleet, handle trips, broadcast live location, and view earnings.

Pages: `owner/dashboard.html`, `owner/vehicles.html`, `owner/trips.html`, `owner/earnings.html`.

Tasks:
1. **Dashboard:** fleet summary, upcoming trips, training completion status (locked banner if incomplete), earnings snapshot.
2. **Training:** list of modules with status badges; "Mark complete" button.
3. **Vehicles:** add/edit/withdraw wizard.
4. **Trips page:**
   - Upcoming trips list; "Start Trip" button (sends `PATCH .../start`).
   - Active trip view:
     - "Complete Trip" button.
     - **Location broadcaster:** "Share My Location" toggle that, when on, reads `navigator.geolocation.watchPosition()` every 10 seconds and POSTs to `.../tracker/ping`.
     - Waypoint checklist: tap a stop to call `.../arrive`.
     - Text status input: car owner types a note sent as `note` in the next ping.
5. **Earnings:** summary cards (lifetime net, pending payout, next payout date), ledger table, CSV export.

Verification: Car owner starts trip -> enables location sharing -> tourist's tracker page updates within 15 seconds.

---

### Phase 19 -- Admin Frontend
**Goal:** Admin can do everything in Sections 4.12 and 4.13 through the UI.

Pages: `admin/dashboard.html`, `admin/verifications.html`, `admin/kpis.html`, `admin/disputes.html`.

Tasks:
1. Dashboard: headline KPIs, pending verifications queue, open disputes, KYC manual-review count.
2. Verifications: tabs for Car Owners / Vehicles / Tourist KYC; approve/reject with reason.
3. KPI page: Chart.js charts (bookings over time, revenue by trip type, fleet utilisation, conversion funnel with KYC step, car owner performance table, tracker adoption %).
4. Disputes: list, detail, refund actions.
5. Users management: search, role filter, suspend/unsuspend, KYC status badge.

Verification: KPI numbers match API; every admin action writes to `audit_log`.

---

### Phase 20 -- Hardening
**Goal:** Safe to run in production.

Tasks:
1. Rate limiting: login 5/min/IP, signup 3/min/IP, tracker ping 1/sec/booking (prevent GPS spam).
2. Input validation: Pydantic schemas with length/format constraints; `extra='forbid'`.
3. File upload safety: content-type sniff, max size, randomise filenames.
4. All config from env vars.
5. Structured JSON logs; never log PII or tokens.
6. Nightly DB backup (14-day rotation).
7. HTTPS via Caddy/Traefik in docker-compose.
8. Security headers: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Content-Security-Policy`.
9. Tracker trail cleanup job (delete pings older than 90 days from completed trips).

Verification: `bandit` on backend; ZAP baseline scan; all critical/high issues resolved.

---

### Phase 21 -- Testing, Docs, Launch Prep

Tasks:
1. 70%+ backend test coverage; 100% on critical paths.
2. Integration tests: full user journeys with `httpx`.
3. README: local dev setup, prod deploy, env var reference.
4. API docs: review every endpoint in `/docs`.
5. Smoke test script: signup -> KYC -> browse -> book -> pay -> start -> ping location -> complete -> review.

Verification: Smoke test passes against fresh deploy in under 5 minutes.

---

## 6. Cross-Cutting Concerns

- **Time zones:** store UTC; display Africa/Kampala (UTC+3).
- **Currencies:** tourist prices in USD; UGX equivalent via config exchange rate.
- **Money math:** store amounts as integer cents; display as decimals.
- **Tracker coordinates:** store as REAL (7 decimal places). Never round for storage.
- **Idempotency keys:** required on `POST /api/bookings` and `/api/payments/initiate`.
- **Pagination:** default 20, max 100 on all list endpoints.
- **Accessibility:** labels on all forms, visible focus states, WCAG AA contrast.

---

## 7. Out of Scope for v1

- Self-drive / no-driver option (deliberate product decision).
- A separate driver role distinct from the car owner.
- Real-time WebSockets (polling covers the tracker in v1).
- Mobile apps (responsive web only).
- Multi-currency checkout.
- Loyalty / referral codes.
- Partner portal.
- Advanced fraud detection.
- PDF insurance certificates.
- Public API for third parties.

---

## 8. Definition of Done (v1)

1. All 21 phases verified.
2. A tourist can sign up, complete KYC, browse, book, pay, track the trip live on a map, and submit a review.
3. A car owner can complete onboarding, submit a vehicle, get verified, start and run a trip with live location sharing, and view earnings.
4. An admin can verify car owners/vehicles, review KYC cases, resolve disputes, and see live KPIs including tracker adoption.
5. A tourist without approved KYC cannot create a booking under any code path (automated test).
6. A vehicle whose car owner has not completed training cannot be booked.
7. Trip tracker pings are rejected when the booking is not `in_progress`.
8. The smoke test passes against a freshly deployed instance.

---

## 9. Build Order Summary

```
Week 1: Phases 1-3    (scaffolding, data model, auth)
Week 2: Phases 4-6    (vehicle verification, car owner onboarding, search)
Week 3: Phases 7-9    (tourist KYC, booking creation, payments)
Week 4: Phase 10      (trip tracker -- backend + data)
Week 5: Phases 11-15  (reviews, messaging, notifications, admin tools, analytics)
Week 6: Phases 16-18  (tourist + car owner frontend including tracker UI)
Week 7: Phases 19-21  (admin UI, hardening, launch prep)
```

The app is end-to-end testable after Phase 9. The tracker is layered on top of the confirmed
booking lifecycle, making Phase 10 a clean addition without backtracking.

---

*End of plan -- v2 (Car Owner Model + Trip Tracker).*
