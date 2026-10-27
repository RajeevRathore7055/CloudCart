from fastapi import APIRouter, HTTPException, Request
from app.db import query_all, query_one
from app.templating import render

router = APIRouter(tags=["shop"])

SORTS = {"price_asc": "p.price ASC", "price_desc": "p.price DESC", "newest": "p.id DESC"}
BASE = "SELECT p.*, c.name AS category FROM products p JOIN categories c ON c.id = p.category_id"


def search_products(q="", category="", sort="newest"):
    where, params = [], []
    if q:
        where.append("(p.name LIKE %s OR p.description LIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    if category.isdigit():
        where.append("p.category_id = %s")
        params.append(int(category))
    sql = BASE + (" WHERE " + " AND ".join(where) if where else "")
    sql += " ORDER BY " + SORTS.get(sort, SORTS["newest"])  # whitelisted -> safe
    return query_all(sql, params)


@router.get("/")
def home(request: Request):
    featured = query_all(BASE + " WHERE p.is_featured = 1 ORDER BY p.id LIMIT 8")
    return render(request, "home.html", featured=featured)


@router.get("/products")
def products(request: Request, q: str = "", category: str = "", sort: str = "newest"):
    q = q.strip()[:100]
    items = search_products(q, category, sort)
    return render(request, "products.html", products=items, q=q, category=category, sort=sort)


@router.get("/products/{product_id}")
def product_detail(request: Request, product_id: int):
    p = query_one(BASE + " WHERE p.id = %s", (product_id,))
    if not p:
        raise HTTPException(404, "Product not found")
    related = query_all(BASE + " WHERE p.category_id=%s AND p.id<>%s LIMIT 4", (p["category_id"], product_id))
    return render(request, "product_detail.html", p=p, related=related)
