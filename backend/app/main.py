from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from backend.app.database.base import Base
from backend.app.database.connection import engine

from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.ticket import SupportTicket

from backend.app.routes.user_routes import router as user_router
from backend.app.routes.product_routes import router as product_router
from backend.app.routes.order_routes import router as order_router
from backend.app.routes.ticket_routes import router as ticket_router
from backend.app.routes.ai_routes import router as ai_router
from backend.app.routes.agent_routes import router as agent_router


app = FastAPI(
    title="SupportFlow AI",
    description="Agentic AI Customer Support Platform",
    version="1.0.0"
)


# =========================
# CORS CONFIGURATION
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://supportflow-ai-1.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# ROUTES
# =========================

app.include_router(user_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(ticket_router)
app.include_router(ai_router)
app.include_router(agent_router)


# =========================
# DATABASE
# =========================

Base.metadata.create_all(bind=engine)


# =========================
# ROOT
# =========================

@app.get("/")
def root():
    return {
        "message": "SupportFlow AI backend is running!"
    }


# =========================
# HEALTH CHECK
# =========================

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }