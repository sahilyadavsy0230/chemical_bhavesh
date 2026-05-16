# ============================================================
# app/models/project.py - Project Model
# ============================================================

import datetime
from app import db


class Project(db.Model):
    """
    Represents a user's saved design project.
    A project groups one or more equipment designs together.
    """

    __tablename__ = 'projects'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        nullable=True)
    status      = db.Column(db.String(30),  default='active')  # active | completed | archived

    # Project metadata
    industry    = db.Column(db.String(100), nullable=True)
    tags        = db.Column(db.String(300), nullable=True)   # comma-separated

    # Timestamps
    created_at  = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                            onupdate=datetime.datetime.utcnow)

    # Relationships
    designs     = db.relationship('EquipmentDesign', backref='project', lazy='dynamic',
                                  cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'description': self.description,
            'status':      self.status,
            'industry':    self.industry,
            'tags':        self.tags.split(',') if self.tags else [],
            'created_at':  self.created_at.isoformat() if self.created_at else None,
            'design_count': self.designs.count(),
        }

    def __repr__(self):
        return f'<Project {self.name}>'
