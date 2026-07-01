from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import agents_admin, companies, health, ingestion, patterns, search, swatches, trade
from app.db.qdrant_client import get_qdrant_client
from app.db.qdrant_collections import ensure_collections
from app.kg.neo4j_client import close_neo4j_driver, get_neo4j_driver
from app.kg.schema import apply_schema
from app.logging_conf import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup")
    await ensure_collections(get_qdrant_client())
    await apply_schema(get_neo4j_driver())
    yield
    await close_neo4j_driver()
    logger.info("shutdown")


app = FastAPI(
    title="Japan Fashion & Handloom Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Without this, an unhandled exception is turned into a 500 by Starlette's outer
    ServerErrorMiddleware, which sits *outside* CORSMiddleware - that response never gets CORS
    headers attached. The browser then can't read the response at all and reports it to
    JavaScript as a generic "Failed to fetch" network error instead of a normal HTTP 500,
    hiding the real error. Registering a handler here makes FastAPI treat the exception as
    "handled", so the response passes back through CORSMiddleware normally."""
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(trade.router, prefix="/api/v1")
app.include_router(agents_admin.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(swatches.router, prefix="/api/v1")
app.include_router(patterns.router, prefix="/api/v1")
