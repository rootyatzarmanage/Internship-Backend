1.pip install uv
2.uv sync
 
 
 
Run database migrations
uv run alembic revision --autogenerate -m "create_initial_tables"
1.uv run alembic upgrade head

Seed RBAC roles
 
1.uv run python -m ycpa.seeders.seed_rbac
 
Ubuntu:
source venv/bin/activate

Windows:
.\venv\Scripts\Activate.ps1
.\venv\Scripts\activate.bat

To run :

python run.py
 
 
