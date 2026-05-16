# ============================================================
# app/models/equipment.py - Equipment Design Model
# ============================================================

import datetime
import json
from app import db


class EquipmentDesign(db.Model):
    """
    Stores a single equipment design run including:
    - raw user inputs
    - computed results (JSON)
    - AI suggestions
    - cost estimation
    - path to the generated PDF report
    """

    __tablename__ = 'equipment_designs'

    # ── Keys ─────────────────────────────────────────────────
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False, index=True)
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True,  index=True)

    # ── Equipment Identity ───────────────────────────────────
    equipment_type = db.Column(db.String(50), nullable=False, index=True)
    # Possible values: heat_exchanger | reactor | distillation | evaporator |
    #                  absorber | pump | compressor
    design_name    = db.Column(db.String(200), nullable=True)

    # ── Input / Output (stored as JSON text) ─────────────────
    input_data    = db.Column(db.Text, nullable=False)   # JSON dict of user inputs
    result_data   = db.Column(db.Text, nullable=True)    # JSON dict of calculated results
    ai_suggestions = db.Column(db.Text, nullable=True)   # AI optimisation suggestions (text)

    # ── Cost & Efficiency ────────────────────────────────────
    estimated_cost     = db.Column(db.Float, nullable=True)   # USD
    efficiency_score   = db.Column(db.Float, nullable=True)   # 0–100 %
    energy_consumption = db.Column(db.Float, nullable=True)   # kW

    # ── Report ───────────────────────────────────────────────
    report_path  = db.Column(db.String(400), nullable=True)   # relative path to PDF
    report_generated = db.Column(db.Boolean, default=False)

    # ── Status ───────────────────────────────────────────────
    status = db.Column(db.String(20), default='completed')  # completed | draft | error

    # ── Timestamps ───────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                           onupdate=datetime.datetime.utcnow)

    # ── JSON helpers ─────────────────────────────────────────

    def get_inputs(self) -> dict:
        """Deserialise stored JSON inputs."""
        try:
            return json.loads(self.input_data) if self.input_data else {}
        except json.JSONDecodeError:
            return {}

    def set_inputs(self, data: dict) -> None:
        self.input_data = json.dumps(data)

    def get_results(self) -> dict:
        try:
            return json.loads(self.result_data) if self.result_data else {}
        except json.JSONDecodeError:
            return {}

    def set_results(self, data: dict) -> None:
        self.result_data = json.dumps(data)

    # ── Serialisation ────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            'id':               self.id,
            'equipment_type':   self.equipment_type,
            'design_name':      self.design_name,
            'status':           self.status,
            'estimated_cost':   self.estimated_cost,
            'efficiency_score': self.efficiency_score,
            'energy_consumption': self.energy_consumption,
            'report_generated': self.report_generated,
            'created_at':       self.created_at.isoformat() if self.created_at else None,
            'inputs':           self.get_inputs(),
            'results':          self.get_results(),
        }

    def __repr__(self):
        return f'<EquipmentDesign {self.equipment_type} #{self.id}>'
