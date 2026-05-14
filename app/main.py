from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import auth,users,vehicles,bookings,payments,admin

app = FastAPI(
    title="Kari Vari Uganda",
    description="Car Rental Marketplace Platform",
    version="1.0.0"
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(vehicles.router)
app.include_router(bookings.router)
app.include_router(payments.router)
app.include_router(admin.router)

# create route to render index.html
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "Server is running"
    }