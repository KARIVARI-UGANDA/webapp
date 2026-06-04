import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.routers import (
    admin,
    auth,
    bookings,
    kyc,
    messages,
    notifications,
    payments,
    reviews,
    users,
    vehicles,
)

app = FastAPI(
    title="Karivari Uganda",
    description="4×4 vehicle marketplace connecting customers with verified Ugandan car owners.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
os.makedirs("uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="app/templates")

# API routers — all under /api
API = "/api"
app.include_router(auth.router, prefix=API)
app.include_router(users.router, prefix=API)
app.include_router(vehicles.router, prefix=API)
app.include_router(bookings.router, prefix=API)
app.include_router(payments.router, prefix=API)
app.include_router(reviews.router, prefix=API)
app.include_router(messages.router, prefix=API)
app.include_router(notifications.router, prefix=API)
app.include_router(kyc.router, prefix=API)
app.include_router(admin.router, prefix=API)


@app.get("/api/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": app.version}


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/register.html")


# Owner portal
@app.get("/owner/login")
def owner_login_page(request: Request):
    return templates.TemplateResponse(request, "owner/login.html")


@app.get("/owner/register")
def owner_register_page(request: Request):
    return templates.TemplateResponse(request, "owner/register.html")


@app.get("/owner/dashboard")
def owner_dashboard(request: Request):
    return templates.TemplateResponse(request, "owner/dashboard.html")


# Customer portal
@app.get("/dashboard")
def customer_dashboard(request: Request):
    return templates.TemplateResponse(request, "customer/dashboard.html")


@app.get("/vehicles")
def vehicle_listings(request: Request):
    return templates.TemplateResponse(request, "customer/vehicles.html")


@app.get("/vehicles/{vehicle_id}")
def vehicle_detail(request: Request, vehicle_id: str):
    return templates.TemplateResponse(request, "customer/vehicle_detail.html")


@app.get("/checkout")
def checkout_page(request: Request):
    return templates.TemplateResponse(request, "customer/checkout.html")


@app.get("/my-bookings")
def my_bookings_page(request: Request):
    return templates.TemplateResponse(request, "customer/my_bookings.html")


@app.get("/my-payments")
def my_payments_page(request: Request):
    return templates.TemplateResponse(request, "customer/my_payments.html")


@app.get("/support")
def support_page(request: Request):
    return templates.TemplateResponse(request, "customer/support.html")


@app.get("/settings")
def settings_page(request: Request):
    return templates.TemplateResponse(request, "settings.html")


# Admin portal
@app.get("/admin/login")
def admin_login_page(request: Request):
    return templates.TemplateResponse(request, "admin/login.html")


@app.get("/admin/dashboard")
def admin_dashboard(request: Request):
    return templates.TemplateResponse(request, "admin/dashboard.html")


@app.get("/how-it-works")
def how_it_works_page(request: Request):
    return templates.TemplateResponse(request, "how-it-works.html")


@app.get("/admin/bookings")
def admin_bookings_redirect(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin/dashboard", status_code=302)


@app.get("/admin/users")
def admin_users_redirect(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin/dashboard", status_code=302)
