from fastapi import APIRouter, HTTPException
from app.routes.shop import BASE, search_products
from app.db import query_one
from app.services.storage import image_url

router = APIRouter(prefix="/api", tags=["REST API"])


def _out(p):
    p = dict(p)
    p["image"] = image_url(p.pop("image_url", None))
    return p


@router.get("/products")
def api_products(q: str = "", category: str = "", sort: str = "newest"):
    """List/search products (JSON). Try it live at /docs"""
    return [_out(p) for p in search_products(q.strip()[:100], category, sort)]


@router.get("/products/{product_id}")
def api_product(product_id: int):
    p = query_one(BASE + " WHERE p.id=%s", (product_id,))
    if not p:
        raise HTTPException(404, "Product not found")
    return _out(p)
