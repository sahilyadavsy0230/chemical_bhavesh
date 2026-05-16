# app/models/__init__.py
# Import all models so Flask-Migrate can detect them

from app.models.user      import User
from app.models.project   import Project
from app.models.equipment import EquipmentDesign
from app.models.chat      import ChatHistory
