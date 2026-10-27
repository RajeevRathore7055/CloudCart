import re
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import execute, query_one
from app.security import flash, safe_next
from app.templating import render

router = APIRouter(tags=["auth"])
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _start_session(request: Request, user: dict):
    request.session.clear()  # prevents session fixation
    request.session["user_id"] = user["id"]
    request.session["name"] = user["name"]
    request.session["role"] = user["role"]


@router.get("/register")
def register_page(request: Request):
    return render(request, "register.html", form={}, errors=[])


@router.post("/register")
def register(request: Request, name: str = Form(""), email: str = Form(""), password: str = Form(""), confirm: str = Form("")):
    name, email = name.strip(), email.strip().lower()
    errors = []
    if len(name) < 2 or len(name) > 100:
        errors.append("Name must be 2-100 characters.")
    if not EMAIL_RE.match(email) or len(email) > 150:
        errors.append("Enter a valid email address.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if password != confirm:
        errors.append("Passwords do not match.")
    if not errors and query_one("SELECT id FROM users WHERE email=%s", (email,)):
        errors.append("This email is already registered.")
    if errors:
        return render(request, "register.html", status_code=400, form={"name": name, "email": email}, errors=errors)
    uid = execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s,%s,%s,'customer')",
        (name, email, generate_password_hash(password)),
    )
    _start_session(request, {"id": uid, "name": name, "role": "customer"})
    flash(request, f"Welcome to CloudCart, {name}!", "success")
    return RedirectResponse("/", status_code=303)


@router.get("/login")
def login_page(request: Request, next: str = "/"):
    return render(request, "login.html", next=safe_next(next), errors=[], email="")


@router.post("/login")
def login(request: Request, email: str = Form(""), password: str = Form(""), next: str = Form("/")):
    email = email.strip().lower()
    row = query_one("SELECT id, name, role, password_hash FROM users WHERE email=%s", (email,))
    if not row or not check_password_hash(row["password_hash"], password):
        return render(request, "login.html", status_code=401, next=safe_next(next), email=email, errors=["Invalid email or password."])
    _start_session(request, row)
    flash(request, f"Welcome back, {row['name']}!", "success")
    if row["role"] == "admin" and next in ("/", ""):
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse(safe_next(next), status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "You have been logged out.", "info")
    return RedirectResponse("/", status_code=303)
