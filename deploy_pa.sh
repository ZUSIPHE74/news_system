#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "=== Starting PythonAnywhere News System Deployment ==="

# 1. Clone or Pull the Git Repository
PROJECT_DIR="$HOME/news_system"
REPO_URL="https://github.com/ZUSIPHE74/news_system.git"

if [ -d "$PROJECT_DIR" ]; then
    echo ">>> Project directory exists. Pulling latest changes from GitHub..."
    cd "$PROJECT_DIR"
    git pull origin main
else
    echo ">>> Cloning repository from GitHub..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# 2. Setup Virtual Environment
VENV_DIR="$HOME/.virtualenvs/news-env"
if [ ! -d "$VENV_DIR" ]; then
    echo ">>> Creating a virtual environment (Python 3.10)..."
    mkdir -p "$HOME/.virtualenvs"
    python3.10 -m venv "$VENV_DIR"
fi

echo ">>> Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip and install dependencies
echo ">>> Installing python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ">>> Creating .env file from .env.example..."
    cp .env.example .env
fi

# 4. Database Migrations
echo ">>> Running database migrations..."
python manage.py migrate

# 5. Collect Static Files
echo ">>> Collecting static files..."
python manage.py collectstatic --noinput

# 6. Seed mock articles (optional, but ensures application has data)
echo ">>> Seeding initial data..."
python seed_se_articles.py || echo "Warning: Seeding script skipped or encountered an issue, continuing..."

echo "=== Setup Completed Successfully! ==="
echo "Please proceed to configure the Web App in your PythonAnywhere Dashboard."
