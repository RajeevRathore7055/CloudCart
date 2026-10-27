# CloudCart - Cloud-Based E-Commerce Platform

A simple, viva-friendly e-commerce app built with **FastAPI + MySQL + Bootstrap**, designed to be deployed on **AWS** (EC2, RDS, S3, CloudFront, CloudWatch, IAM, VPC, ALB, Auto Scaling).

## 1. Features
- Customer: register/login/logout (hashed passwords), product list, search, category filter, price sort, product details, cart (add/remove/+/-), checkout (mock payment), order confirmation, order history, order status tracking.
- Admin: dashboard (users/products/orders/sales), add/edit/delete products (image upload), view users, view orders, update order status.
- REST API + auto docs: `/api/products`, `/docs` (Swagger UI), `/health` (for Load Balancer).

## 2. Tech stack
Python 3.12, FastAPI, Jinja2 templates, PyMySQL (parameterized SQL), MySQL 8, Bootstrap 5, vanilla JS, Gunicorn + Uvicorn, Nginx, Git/GitHub.

## 3. Folder structure
```
CloudCart/
├── app/
│   ├── main.py          # FastAPI app, middleware, error handlers, /health
│   ├── config.py        # reads environment variables (.env)
│   ├── db.py            # MySQL connection + safe query helpers
│   ├── security.py      # login_required / admin_required, flash, safe redirect
│   ├── templating.py    # Jinja2 setup + shared page context
│   ├── routes/          # auth, shop, cart, orders, admin, api
│   ├── services/storage.py   # product images: local folder OR S3 (+CloudFront URL)
│   ├── templates/       # HTML pages (admin/ for admin pages)
│   └── static/          # css, js, images
├── database/            # schema.sql, sample_data.sql
├── scripts/             # init_db.py (create tables/data/users), make_images.py
├── tests/test_app.py    # 14 automated tests
├── deploy/              # ec2_setup.sh, update.sh, cloudwatch-agent-config.json
├── .github/workflows/ci.yml   # GitHub Actions: install + test on every push
├── .env.example  .gitignore  requirements.txt  pytest.ini
```

## 4. Local setup (Windows PowerShell)
```powershell
cd CloudCart
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env        # then edit .env (DB password, SECRET_KEY)
```
Generate SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`

## 5. Database setup
In MySQL Workbench (root) run:
```sql
CREATE DATABASE IF NOT EXISTS cloudcart CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'cloudcart_user'@'localhost' IDENTIFIED BY 'YourPasswordHere';
GRANT ALL PRIVILEGES ON cloudcart.* TO 'cloudcart_user'@'localhost';
FLUSH PRIVILEGES;
```
Use the same password in `.env`. Then:
```powershell
python -m scripts.init_db          # tables + sample data + admin/demo users
python -m scripts.init_db --reset  # (optional) wipe and rebuild
```
Run the app: `uvicorn app.main:app --reload` -> http://127.0.0.1:8000

Logins: admin `admin@cloudcart.com` / `Admin@123` | customer `demo@cloudcart.com` / `Customer@123`

## 6. Environment variables
`DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, SECRET_KEY, AWS_REGION, S3_BUCKET_NAME, IMAGE_BASE_URL, COOKIE_SECURE, ADMIN_EMAIL, ADMIN_PASSWORD`. Never commit `.env`.

## 7. AWS deployment overview
```
User -> CloudFront / ALB -> EC2 (Nginx -> Gunicorn/FastAPI) -> RDS MySQL (private)
                              |-> S3 (images, via IAM Role)      CloudWatch (logs+metrics)
```
On EC2 (Ubuntu 24.04): `git clone <repo>; cd CloudCart; cp .env.example .env; nano .env; bash deploy/ec2_setup.sh`
Set `DATABASE_HOST` to the RDS endpoint. For S3: set `AWS_REGION`, `S3_BUCKET_NAME` (and `IMAGE_BASE_URL` = CloudFront URL), attach an IAM Role with S3 access to the EC2 instance, and upload demo images: `aws s3 sync app/static/images s3://<bucket>/`.
Update later with `bash deploy/update.sh`. ALB health-check path: `/health`.

## 8. Cloud services used
EC2 (compute), RDS (managed MySQL), S3 (images), IAM (EC2 role, least privilege), VPC + Security Groups (network), CloudWatch (metrics/logs), CloudFront (CDN), ALB + Auto Scaling (scalability/availability), automated RDS backups.

## 9. Security
Password hashing (Werkzeug), parameterized SQL (no SQL injection), session cookies (HttpOnly, SameSite=Lax, signed), admin authorization on every `/admin` route, input validation, upload validation (type + size), open-redirect protection, secrets only in environment variables, `.gitignore` for `.env`.

## 10. Testing
`pytest -v` (needs MySQL + `init_db`). Covers registration, login, invalid login, search, filter, SQL-injection attempt, cart add/remove, checkout, order creation + stock reduction, admin login, add/edit/delete product, order status update.

## 11. Future improvements
Real payment gateway, email notifications, product reviews, pagination, HTTPS with ACM certificate, Docker/ECS, CodePipeline CI/CD.
