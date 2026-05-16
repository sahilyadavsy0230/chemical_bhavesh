# ============================================================
# app/models/user.py - User Model
# ============================================================

import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(UserMixin, db.Model):
    """
    User account model.
    Stores authentication credentials, profile data, and preferences.
    """

    __tablename__ = 'users'

    # ── Primary Key ──────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ── Authentication ───────────────────────────────────────
    username     = db.Column(db.String(80),  unique=True, nullable=False, index=True)
    email        = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # ── Profile ──────────────────────────────────────────────
    full_name    = db.Column(db.String(150), nullable=True)
    institution  = db.Column(db.String(200), nullable=True)
    department   = db.Column(db.String(200), nullable=True)
    bio          = db.Column(db.Text,        nullable=True)
    avatar_url   = db.Column(db.String(300), nullable=True,
                             default='/static/images/default_avatar.png')

    # ── Roles & Permissions ──────────────────────────────────
    role         = db.Column(db.String(20), nullable=False, default='user')
    # roles: 'user', 'admin', 'engineer'
    is_active    = db.Column(db.Boolean, default=True, nullable=False)
    is_verified  = db.Column(db.Boolean, default=False, nullable=False)

    # ── Preferences ──────────────────────────────────────────
    theme_preference = db.Column(db.String(10), default='dark')   # 'dark' | 'light'
    unit_system      = db.Column(db.String(10), default='SI')     # 'SI' | 'Imperial'

    # ── Timestamps ───────────────────────────────────────────
    created_at   = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_login   = db.Column(db.DateTime, nullable=True)
    updated_at   = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                             onupdate=datetime.datetime.utcnow)

    # ── Relationships ────────────────────────────────────────
    projects     = db.relationship('Project',        backref='owner',    lazy='dynamic',
                                   cascade='all, delete-orphan')
    chat_history = db.relationship('ChatHistory',    backref='user',     lazy='dynamic',
                                   cascade='all, delete-orphan')
    designs      = db.relationship('EquipmentDesign', backref='designer', lazy='dynamic',
                                   cascade='all, delete-orphan')

    # ── Password Methods ─────────────────────────────────────

    def set_password(self, password: str) -> None:
        """Hash and store the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    # ── Helpers ──────────────────────────────────────────────

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

    def to_dict(self) -> dict:
        """Serialise user data (safe for API responses — excludes password)."""
        return {
            'id':          self.id,
            'username':    self.username,
            'email':       self.email,
            'full_name':   self.full_name,
            'institution': self.institution,
            'role':        self.role,
            'theme':       self.theme_preference,
            'unit_system': self.unit_system,
            'created_at':  self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f'<User {self.username} ({self.role})>'
