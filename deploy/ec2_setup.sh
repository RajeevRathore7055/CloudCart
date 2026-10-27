#!/bin/bash
# Run ON the EC2 instance (Ubuntu 24.04) after cloning the repo:
#   git clone https://github.com/<you>/CloudCart.git && cd CloudCart
#   cp .env.example .env && nano .env      # put RDS endpoint, password, secret key
#   bash deploy/ec2_setup.sh
set -e
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="$(whoami)"

sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip nginx git mysql-client

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# Create DB tables + sample data (works with RDS because .env points to it)
cd "$APP_DIR" && "$APP_DIR/.venv/bin/python" -m scripts.init_db

# systemd service: keeps the app running and restarts it on crash/reboot
sudo tee /etc/systemd/system/cloudcart.service >/dev/null <<UNIT
[Unit]
Description=CloudCart FastAPI app
After=network.target

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -b 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

# nginx: port 80 -> gunicorn on 8000
sudo tee /etc/nginx/sites-available/cloudcart >/dev/null <<'NGINX'
server {
    listen 80 default_server;
    client_max_body_size 5M;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
sudo ln -sf /etc/nginx/sites-available/cloudcart /etc/nginx/sites-enabled/cloudcart
sudo rm -f /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable --now cloudcart
sudo nginx -t && sudo systemctl restart nginx
echo "DONE. Open http://<EC2-public-IP>/  and  http://<EC2-public-IP>/health"
