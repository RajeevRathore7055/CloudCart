import re
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.db import get_connection, query_all, query_one
from app.routes.cart import get_cart
from app.security import flash, login_required
from app.templating import render

router = APIRouter(tags=["orders"])
PHONE_RE = re.compile(r"^[0-9+\-\s]{10,15}$")
STATUSES = ["Placed", "Processing", "Shipped", "Delivered"]


@router.get("/checkout")
def checkout_page(request: Request, user=Depends(login_required)):
    items, total = get_cart(user["id"])
    if not items:
        flash(request, "Your cart is empty.", "error")
        return RedirectResponse("/cart", status_code=303)
    return render(request, "checkout.html", items=items, total=total, form={"name": user["name"]}, errors=[])


@router.post("/checkout")
def place_order(request: Request, name: str = Form(""), address: str = Form(""), phone: str = Form(""),
                user=Depends(login_required)):
    name, address, phone = name.strip(), address.strip(), phone.strip()
    items, total = get_cart(user["id"])
    errors = []
    if not items:
        flash(request, "Your cart is empty.", "error")
        return RedirectResponse("/cart", status_code=303)
    if len(name) < 2:
        errors.append("Enter your full name.")
    if len(address) < 10:
        errors.append("Enter a complete address (min 10 characters).")
    if not PHONE_RE.match(phone):
        errors.append("Enter a valid phone number (10-15 digits).")
    if errors:
        return render(request, "checkout.html", status_code=400, items=items, total=total,
                      form={"name": name, "address": address, "phone": phone}, errors=errors)

    # One database transaction: either the whole order succeeds or nothing changes.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT c.product_id, c.quantity, p.name, p.price, p.stock FROM cart_items c "
                "JOIN products p ON p.id=c.product_id WHERE c.user_id=%s FOR UPDATE", (user["id"],))
            rows = cur.fetchall()
            for r in rows:
                if r["quantity"] > r["stock"]:
                    conn.rollback()
                    flash(request, f"Sorry, only {r['stock']} left for {r['name']}.", "error")
                    return RedirectResponse("/cart", status_code=303)
            order_total = sum(r["price"] * r["quantity"] for r in rows)
            cur.execute(
                "INSERT INTO orders (user_id, customer_name, address, phone, total_amount) VALUES (%s,%s,%s,%s,%s)",
                (user["id"], name, address, phone, order_total))
            order_id = cur.lastrowid
            for r in rows:
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity) VALUES (%s,%s,%s,%s,%s)",
                    (order_id, r["product_id"], r["name"], r["price"], r["quantity"]))
                cur.execute("UPDATE products SET stock = stock - %s WHERE id=%s", (r["quantity"], r["product_id"]))
            cur.execute("DELETE FROM cart_items WHERE user_id=%s", (user["id"],))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    flash(request, f"Order #{order_id} placed successfully! (Mock payment completed)", "success")
    return RedirectResponse(f"/orders/{order_id}?placed=1", status_code=303)


@router.get("/orders")
def order_history(request: Request, user=Depends(login_required)):
    orders = query_all("SELECT * FROM orders WHERE user_id=%s ORDER BY id DESC", (user["id"],))
    return render(request, "orders.html", orders=orders)


@router.get("/orders/{order_id}")
def order_detail(request: Request, order_id: int, placed: int = 0, user=Depends(login_required)):
    order = query_one("SELECT * FROM orders WHERE id=%s", (order_id,))
    if not order or (order["user_id"] != user["id"] and user["role"] != "admin"):
        raise HTTPException(404, "Order not found")
    items = query_all("SELECT * FROM order_items WHERE order_id=%s", (order_id,))
    return render(request, "order_detail.html", order=order, items=items, placed=bool(placed), statuses=STATUSES)
