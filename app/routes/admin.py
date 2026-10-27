from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse

from app.db import execute, query_all, query_one
from app.routes.orders import STATUSES
from app.security import admin_required, flash
from app.services.storage import save_image
from app.templating import render

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(admin_required)])


@router.get("")
def dashboard(request: Request):
    stats = {
        "users": query_one("SELECT COUNT(*) n FROM users")["n"],
        "products": query_one("SELECT COUNT(*) n FROM products")["n"],
        "orders": query_one("SELECT COUNT(*) n FROM orders")["n"],
        "sales": query_one("SELECT COALESCE(SUM(total_amount),0) n FROM orders")["n"],
    }
    recent = query_all("SELECT * FROM orders ORDER BY id DESC LIMIT 5")
    return render(request, "admin/dashboard.html", stats=stats, recent=recent)


@router.get("/products")
def products(request: Request):
    items = query_all("SELECT p.*, c.name AS category FROM products p JOIN categories c ON c.id=p.category_id ORDER BY p.id DESC")
    return render(request, "admin/products.html", products=items)


def _parse_product(name, category_id, price, stock, description):
    errors, data = [], {}
    data["name"] = name.strip()
    data["description"] = description.strip()
    if not data["name"] or len(data["name"]) > 150:
        errors.append("Product name is required (max 150 chars).")
    try:
        data["price"] = Decimal(price)
        if data["price"] < 0:
            raise InvalidOperation
    except InvalidOperation:
        errors.append("Enter a valid price.")
    try:
        data["stock"] = int(stock)
        if data["stock"] < 0:
            raise ValueError
    except ValueError:
        errors.append("Stock must be a non-negative number.")
    try:
        data["category_id"] = int(category_id)
        if not query_one("SELECT id FROM categories WHERE id=%s", (data["category_id"],)):
            raise ValueError
    except ValueError:
        errors.append("Select a valid category.")
    return data, errors


@router.get("/products/new")
def new_product_page(request: Request):
    return render(request, "admin/product_form.html", p={}, errors=[], title="Add Product")


@router.post("/products/new")
def create_product(request: Request, name: str = Form(""), category_id: str = Form(""), price: str = Form(""),
                   stock: str = Form(""), description: str = Form(""), is_featured: Optional[str] = Form(None),
                   image: Optional[UploadFile] = File(None)):
    data, errors = _parse_product(name, category_id, price, stock, description)
    filename = None
    if not errors and image and image.filename:
        try:
            filename = save_image(image)
        except ValueError as e:
            errors.append(str(e))
    if errors:
        return render(request, "admin/product_form.html", status_code=400, p=dict(data, category_id=category_id, price=price, stock=stock), errors=errors, title="Add Product")
    execute(
        "INSERT INTO products (category_id, name, description, price, stock, image_url, is_featured) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (data["category_id"], data["name"], data["description"], data["price"], data["stock"], filename, 1 if is_featured else 0))
    flash(request, "Product added.", "success")
    return RedirectResponse("/admin/products", status_code=303)


@router.get("/products/{pid}/edit")
def edit_product_page(request: Request, pid: int):
    p = query_one("SELECT * FROM products WHERE id=%s", (pid,))
    if not p:
        raise HTTPException(404, "Product not found")
    return render(request, "admin/product_form.html", p=p, errors=[], title="Edit Product")


@router.post("/products/{pid}/edit")
def update_product(request: Request, pid: int, name: str = Form(""), category_id: str = Form(""), price: str = Form(""),
                   stock: str = Form(""), description: str = Form(""), is_featured: Optional[str] = Form(None),
                   image: Optional[UploadFile] = File(None)):
    old = query_one("SELECT * FROM products WHERE id=%s", (pid,))
    if not old:
        raise HTTPException(404, "Product not found")
    data, errors = _parse_product(name, category_id, price, stock, description)
    filename = old["image_url"]
    if not errors and image and image.filename:
        try:
            filename = save_image(image)
        except ValueError as e:
            errors.append(str(e))
    if errors:
        return render(request, "admin/product_form.html", status_code=400, p=dict(old, **data, category_id=category_id), errors=errors, title="Edit Product")
    execute(
        "UPDATE products SET category_id=%s, name=%s, description=%s, price=%s, stock=%s, image_url=%s, is_featured=%s WHERE id=%s",
        (data["category_id"], data["name"], data["description"], data["price"], data["stock"], filename, 1 if is_featured else 0, pid))
    flash(request, "Product updated.", "success")
    return RedirectResponse("/admin/products", status_code=303)


@router.post("/products/{pid}/delete")
def delete_product(request: Request, pid: int):
    execute("DELETE FROM products WHERE id=%s", (pid,))
    flash(request, "Product deleted.", "info")
    return RedirectResponse("/admin/products", status_code=303)


@router.get("/users")
def users(request: Request):
    rows = query_all("SELECT u.id, u.name, u.email, u.role, u.created_at, COUNT(o.id) AS orders "
                     "FROM users u LEFT JOIN orders o ON o.user_id=u.id GROUP BY u.id ORDER BY u.id")
    return render(request, "admin/users.html", users=rows)


@router.get("/orders")
def orders(request: Request):
    rows = query_all("SELECT o.*, u.email FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC")
    return render(request, "admin/orders.html", orders=rows, statuses=STATUSES)


@router.post("/orders/{oid}/status")
def update_status(request: Request, oid: int, status: str = Form(...)):
    if status not in STATUSES:
        raise HTTPException(400, "Invalid status")
    execute("UPDATE orders SET status=%s WHERE id=%s", (status, oid))
    flash(request, f"Order #{oid} marked as {status}.", "success")
    return RedirectResponse("/admin/orders", status_code=303)
