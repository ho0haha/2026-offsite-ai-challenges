"""FastAPI application for the restaurant ordering API."""

from fastapi import FastAPI

from .routes import router

app = FastAPI(
    title="Restaurant Order API",
    description="A simple restaurant ordering system",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
