from pathlib import Path
from fastapi import Request
from fastapi.templating import Jinja2Templates
from app.db import query_all, query_one
from app.security import get_current_user
from app.services.storage import image_url

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
templates.env.filters["inr"] = lambda v: "₹{:,.2f}".format(float(v or 0))
templates.env.globals["img"] = image_url


def render(request: Request, name: str, status_code: int = 200, **ctx):
    user = get_current_user(request)
    cart_count = 0
    if user:
        row = query_one("SELECT COALESCE(SUM(quantity),0) AS n FROM cart_items WHERE user_id=%s", (user["id"],))
        cart_count = int(row["n"])
    ctx.update(
        user=user,
        cart_count=cart_count,
        flashes=request.session.pop("flash", []),
        all_categories=query_all("SELECT id, name FROM categories ORDER BY name"),
    )
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)
