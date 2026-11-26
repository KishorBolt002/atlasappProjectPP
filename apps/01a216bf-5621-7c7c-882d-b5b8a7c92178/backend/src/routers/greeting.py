"""Greeting endpoints: a stateless hello-world greeting and a health probe."""

from fastapi import APIRouter

from src.schemas import Greeting, HealthStatus

DEFAULT_NAME = "World"
GREETING_SUBTITLE = (
    "Your first Atlas app is up and running. Type a name to say hello to someone else."
)

router = APIRouter(prefix="/api", tags=["greeting"])


@router.get("/greeting", response_model=Greeting, summary="Get greeting")
def get_greeting(name: str = DEFAULT_NAME) -> Greeting:
    display_name = name.strip() or DEFAULT_NAME
    return Greeting(message=f"Hello, {display_name}!", subtitle=GREETING_SUBTITLE)


@router.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    return HealthStatus(status="ok")
