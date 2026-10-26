# Windows
# Create virtual environment
python -m venv venv
# Activate virtual environment
.\venv\Scripts\Activate.ps1
# Upgrade pip
python -m pip install --upgrade pip
# Install requirements
pip install -r requirements.txt
# to run 
python run.py

# Ubuntu
# Create virtual environment
python3 -m venv venv
# Activate virtual environment
source venv/bin/activate
# Upgrade pip
python3 -m pip install --upgrade pip
# Install requirements
pip install -r requirements.txt


alembic revision --autogenerate -m "add rbac tables"
alembic upgrade head
python -m ycpa.seeders.seed_rbac
