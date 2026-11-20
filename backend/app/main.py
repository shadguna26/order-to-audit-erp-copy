from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.v1.auth import router as auth_router
from app.api.v1.stock import router as stock_router
from app.api.v1.purchases import router as purchases_router

# Create all database tables on startup (or via Alembic in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Order-to-Audit ERP for Sri Lakshmi Snacks, Tiruchirappalli, Tamil Nadu",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(stock_router, prefix="/api/v1")
app.include_router(purchases_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.COMPANY_NAME,
        "location": "Tiruchirappalli, Tamil Nadu",
        "state_code": settings.COMPANY_STATE_CODE
    }
