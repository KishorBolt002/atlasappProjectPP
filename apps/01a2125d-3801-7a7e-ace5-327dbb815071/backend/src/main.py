"""
FastAPI application entry point.

This file sets up the FastAPI application with proper database connection
using the Cloud SQL connector configured in database.py.
"""

import logging

from fastapi import FastAPI

from src.clients.agents import router as _atlas_agent_sdk_router
from src.routers import health

logging.basicConfig(level=logging.INFO)

# Import your models here

# Note: Tables are created via Alembic migrations, not here
# Run: cd backend && alembic upgrade head
# DO NOT use Base.metadata.create_all() - it bypasses migrations and will fail
# with permission errors in Cloud SQL (app user cannot CREATE TABLES)

app = FastAPI(title="My Application", version="1.0.0")
app.include_router(_atlas_agent_sdk_router)
app.include_router(health.router)


# Add your API endpoints below
# Import routers and include them with app.include_router()
# Example:
# from .routers import items
# app.include_router(items.router, prefix="/api")
