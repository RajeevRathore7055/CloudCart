#!/bin/bash
# Pull latest code from GitHub and restart (run on EC2). Used manually or by CI/CD.
set -e
cd "$(cd "$(dirname "$0")/.." && pwd)"
git pull origin main
.venv/bin/pip install -r requirements.txt
sudo systemctl restart cloudcart
echo "Updated and restarted."
