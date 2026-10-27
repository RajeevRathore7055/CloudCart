from decimal import Decimal
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app.db import execute, query_all, query_one
from app.security import flash, login_required
from app.templating import render

router = APIRouter(tags=["cart"])

CART_SQL = """SELECT c.product_id, c.quantity, p.name, p.price, p.stock, p.image_url,
              (p.price * c.quantity) AS line_total
              FROM cart_items c JOIN products p ON p.id = c.product_id
              WHERE c.user_id = %s ORDER BY c.id"""


def get_cart(user_id):
    items = query_all(CART_SQL, (user_id,))
    total = sum((i["line_total"] for i in items), Decimal("0"))
    return items, total


@router.get("/cart")
def view_cart(request: Request, user=Depends(login_required)):
    items, total = get_cart(user["id"])
    return render(request, "cart.html", items=items, total=total)


@router.post("/cart/add/{product_id}")
def add_to_cart(request: Request, product_id: int, quantity: int = Form(1), user=Depends(login_required)):
    p = query_one("SELECT id, name, stock FROM products WHERE id=%s", (product_id,))
    if not p:
        flash(request, "Product not found.", "error")
        return RedirectResponse("/products", status_code=303)
    existing = query_one("SELECT quantity FROM cart_items WHERE user_id=%s AND product_id=%s", (user["id"], product_id))
    new_qty = (existing["quantity"] if existing else 0) + max(quantity, 1)
    if new_qty > p["stock"]:
        flash(request, f"Only {p['stock']} unit(s) of {p['name']} in stock.", "error")
        return RedirectResponse(f"/products/{product_id}", status_code=303)
    execute(
        "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE quantity = %s",
        (user["id"], product_id, new_qty, new_qty),
    )
    flash(request, f"{p['name']} added to cart.", "success")
    return RedirectResponse("/cart", status_code=303)


@router.post("/cart/update/{product_id}")
def update_cart(request: Request, product_id: int, action: str = Form(...), user=Depends(login_required)):
    row = query_one(
        "SELECT c.quantity, p.stock FROM cart_items c JOIN products p ON p.id=c.product_id "
        "WHERE c.user_id=%s AND c.product_id=%s", (user["id"], product_id))
    if row:
        qty = row["quantity"] + (1 if action == "inc" else -1 if action == "dec" else 0)
        if qty <= 0:
            execute("DELETE FROM cart_items WHERE user_id=%s AND product_id=%s", (user["id"], product_id))
        elif qty > row["stock"]:
            flash(request, "Not enough stock available.", "error")
        else:
            execute("UPDATE cart_items SET quantity=%s WHERE user_id=%s AND product_id=%s", (qty, user["id"], product_id))
    return RedirectResponse("/cart", status_code=303)


@router.post("/cart/remove/{product_id}")
def remove_from_cart(request: Request, product_id: int, user=Depends(login_required)):
    execute("DELETE FROM cart_items WHERE user_id=%s AND product_id=%s", (user["id"], product_id))
    flash(request, "Item removed from cart.", "info")
    return RedirectResponse("/cart", status_code=303)
