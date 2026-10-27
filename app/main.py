import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import query_one
from app.routes import admin, api, auth, cart, orders, shop
from app.security import RedirectException
from app.templating import render

BASE_DIR = Path(__file__).resolve().parent.parent
(BASE_DIR / "logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(BASE_DIR / "logs" / "cloudcart.log")],
)
log = logging.getLogger("cloudcart")

app = FastAPI(title="CloudCart API", description="Cloud-Based E-Commerce Platform", version="1.0.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=settings.COOKIE_SECURE,
    max_age=60 * 60 * 24,
)
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    if not request.url.path.startswith("/static"):
        log.info("%s %s -> %s (%.0f ms)", request.method, request.url.path, response.status_code, (time.time() - start) * 1000)
    return response


@app.exception_handler(RedirectException)
async def redirect_handler(request: Request, exc: RedirectException):
    return RedirectResponse(exc.url, status_code=303)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    return render(request, "error.html", status_code=exc.status_code, code=exc.status_code, message=exc.detail)


@app.get("/health", tags=["system"])
def health():
    """Used by the Application Load Balancer health check."""
    try:
        query_one("SELECT 1 AS ok")
        return {"status": "ok", "database": "up"}
    except Exception as e:  # noqa
        log.error("Health check failed: %s", e)
        return JSONResponse({"status": "error", "database": "down"}, status_code=503)


for r in (auth.router, shop.router, cart.router, orders.router, admin.router, api.router):
    app.include_router(r)
