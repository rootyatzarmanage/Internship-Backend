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

# Super Admin Notifications
# One row per super admin in `notifications`. category_id is a UUID, but there is no category table:
# the 4 categories are hard-coded in ycpa/models/notification.py (class NotificationCategory).
# Never change these ids once they are in the database.

| #  | Category                      | category_id                          | notification_type                  |
|----|-------------------------------|--------------------------------------|------------------------------------|
| 1  | Registered Notification       | 464b29ed-f482-4351-af5d-a50a9eee1dfd | USER_REGISTERED                    |
| 2  | Workspace create Notification | 295caccb-3361-4e6f-8633-7b80c2d7d81c | WORKSPACE_CREATED                  |
| 3  | Project create Notification   | 5369ccd9-d6cd-4020-8a0e-fdc677841500 | PROJECT_CREATED                    |
| 4  | Payment Notification          | f0d8995d-5d0b-4411-8c0c-87f2ad7ebe4c | PAYMENT_RECEIVED, PAYMENT_FAILED   |

alembic upgrade head

GET    /api/v1/super-admin/notifications                 (page, per_page, category_id, is_read, search)
GET    /api/v1/super-admin/notifications/categories
GET    /api/v1/super-admin/notifications/unread-count
PATCH  /api/v1/super-admin/notifications/read-all        (optional category_id)
PATCH  /api/v1/super-admin/notifications/{id}/read
DELETE /api/v1/super-admin/notifications/{id}
