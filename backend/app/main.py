"""FastAPI application entry point.

Run locally:
    uvicorn backend.app.main:app --reload

See docs/backend/SETUP_GUIDE.md.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.database import init_db
from backend.app.routers import analytics, bulk, comments, concerns, policies, reports, retrieval, stance
from backend.app.schemas.common import ErrorDetail, ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="PolicyLens API",
    description="Public policy feedback analysis: comment submission, stance, concern grouping, and reports.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=ErrorDetail(code=str(exc.status_code), message=str(exc.detail))).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # jsonable_encoder is required here: exc.errors() embeds raw exception
    # objects in each error's "ctx" (e.g. the ValueError from a Pydantic
    # field_validator), which plain json.dumps cannot serialize.
    body = ErrorResponse(error=ErrorDetail(code="422", message="Request validation failed")).model_dump()
    body["details"] = jsonable_encoder(exc.errors())
    return JSONResponse(status_code=422, content=body)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(policies.router)
app.include_router(comments.router)
app.include_router(stance.router)
app.include_router(concerns.router)
app.include_router(reports.router)
app.include_router(bulk.router)
app.include_router(retrieval.router)
app.include_router(analytics.router)
