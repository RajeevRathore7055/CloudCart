"""CloudCart tests. Run:  pytest -v   (needs MySQL running + `python -m scripts.init_db` done)"""
import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import query_one
from app.main import app

PASSWORD = "Test@1234"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture(scope="module")
def admin():
    with TestClient(app) as c:
        r = c.post("/login", data={"email": "admin@cloudcart.com", "password": "Admin@123"})
        assert r.status_code == 200
        yield c


def test_health():
    with TestClient(app) as c:
        assert c.get("/health").json()["status"] == "ok"


def test_register(client, email):
    r = client.post("/register", data={"name": "Test User", "email": email, "password": PASSWORD, "confirm": PASSWORD})
    assert r.status_code == 200 and "Welcome to CloudCart" in r.text
    row = query_one("SELECT password_hash FROM users WHERE email=%s", (email,))
    assert row and row["password_hash"] != PASSWORD  # hashed, not plain text


def test_register_duplicate_email(email):
    with TestClient(app) as c:
        r = c.post("/register", data={"name": "X Y", "email": email, "password": PASSWORD, "confirm": PASSWORD})
        assert r.status_code == 400 and "already registered" in r.text


def test_invalid_login():
    with TestClient(app) as c:
        r = c.post("/login", data={"email": "nobody@example.com", "password": "wrong"})
        assert r.status_code == 401 and "Invalid email or password" in r.text


def test_login_and_logout(email):
    with TestClient(app) as c:
        assert "Welcome back" in c.post("/login", data={"email": email, "password": PASSWORD}).text
        assert "Logout" in c.get("/").text
        c.get("/logout")
        assert "Login" in c.get("/").text


def test_product_search_and_filter(client):
    assert "Laptop" in client.get("/products?q=laptop").text or "UltraBook" in client.get("/products?q=laptop").text
    assert "No products match" in client.get("/products?q=zzzzzz").text
    assert "Backpack" in client.get("/products?category=6").text
    items = client.get("/api/products?sort=price_asc").json()
    prices = [float(i["price"]) for i in items]
    assert prices == sorted(prices)


def test_sql_injection_is_harmless(client):
    r = client.get("/products", params={"q": "' OR '1'='1"})
    assert r.status_code == 200 and "No products match" in r.text


def test_cart_requires_login():
    with TestClient(app) as c:
        r = c.get("/cart", follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"].startswith("/login")


def test_cart_checkout_and_order(client):
    first = client.get("/api/products?q=Mouse").json()[0]
    pid, stock_before = first["id"], first["stock"]
    client.post("/cart/add/%d" % pid, data={"quantity": 2})
    assert "GlideX" in client.get("/cart").text
    client.post("/cart/update/%d" % pid, data={"action": "inc"})  # qty 3
    client.post("/cart/update/%d" % pid, data={"action": "dec"})  # qty 2
    client.post("/cart/remove/%d" % pid)
    assert "Your cart is empty" in client.get("/cart").text

    client.post("/cart/add/%d" % pid, data={"quantity": 2})
    bad = client.post("/checkout", data={"name": "A", "address": "short", "phone": "abc"})
    assert bad.status_code == 400
    r = client.post("/checkout", data={"name": "Test User", "address": "12 Park Street, Dehradun", "phone": "9876543210"})
    assert r.status_code == 200 and "Order Confirmed" in r.text
    assert "Placed" in client.get("/orders").text
    assert query_one("SELECT stock FROM products WHERE id=%s", (pid,))["stock"] == stock_before - 2


def test_customer_cannot_open_admin(client):
    assert client.get("/admin").status_code == 403


def test_admin_login_and_dashboard(admin):
    r = admin.get("/admin")
    assert r.status_code == 200 and "Total Sales" in r.text


def test_admin_add_edit_delete_product(admin):
    name = "Test Product " + uuid.uuid4().hex[:6]
    r = admin.post("/admin/products/new", data={"name": name, "category_id": "1", "price": "999.50", "stock": "5", "description": "demo"})
    assert r.status_code == 200 and name in r.text
    pid = query_one("SELECT id FROM products WHERE name=%s", (name,))["id"]
    admin.post(f"/admin/products/{pid}/edit", data={"name": name, "category_id": "1", "price": "1200", "stock": "7", "description": "demo"})
    assert float(query_one("SELECT price FROM products WHERE id=%s", (pid,))["price"]) == 1200.0
    admin.post(f"/admin/products/{pid}/delete")
    assert query_one("SELECT id FROM products WHERE id=%s", (pid,)) is None


def test_admin_rejects_bad_image(admin):
    r = admin.post("/admin/products/new", data={"name": "Bad", "category_id": "1", "price": "1", "stock": "1"},
                   files={"image": ("x.exe", io.BytesIO(b"abc"), "application/octet-stream")})
    assert r.status_code == 400


def test_admin_update_order_status(admin):
    order = query_one("SELECT id FROM orders ORDER BY id DESC LIMIT 1")
    assert order, "run test_cart_checkout_and_order first"
    admin.post(f"/admin/orders/{order['id']}/status", data={"status": "Shipped"})
    assert query_one("SELECT status FROM orders WHERE id=%s", (order["id"],))["status"] == "Shipped"
