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

python -m ycpa.seeders.seed_control_panel_images


json
{
  "section": "ID Configuration",
  "name": "Workspace",
  "fieldtype": 4,
  "name_prefix": "W"
}

{
  "section": "Mail & Settings",
  "name": "Manage Error Mail",
  "fieldtype": 5,
  "value_json": {
    "email": "errors@yatzar.com",
    "cc": ["dev1@yatzar.com", "dev2@yatzar.com"]
  }
}

Mail without CC:

json
{
  "section": "Mail & Settings",
  "name": "Payment Notification",
  "fieldtype": 5,
  "value_json": { "email": "accounts@yatzar.com", "cc": [] }
}


{
  "section": "Policies",
  "name": "Privacy Policy",
  "fieldtype": 3,
  "value": "<h1>Yatzar Manage - Privacy Policy</h1><p><strong>Last Updated:</strong> 26-10-2026</p><h3>1. Introduction</h3><p>Your content here...</p>"
}
json
{
  "section": "Policies",
  "name": "Terms & Service",
  "fieldtype": 3,
  "value": "<h1>Terms of Service</h1><p>Your content here...</p>"
}