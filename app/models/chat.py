# ============================================================
# app/models/chat.py - AI Chat History Model
# ============================================================

import datetime
from app import db


class ChatHistory(db.Model):
    """
    Stores every AI chatbot message exchange.
    Each row is one turn (user message + AI response).
    """

    __tablename__ = 'chat_history'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Context: which design this conversation relates to (optional)
    design_id   = db.Column(db.Integer, db.ForeignKey('equipment_designs.id'),
                            nullable=True, index=True)

    # ── Message Content ──────────────────────────────────────
    user_message = db.Column(db.Text, nullable=False)
    ai_response  = db.Column(db.Text, nullable=False)

    # ── Metadata ────────────────────────────────────────────
    context_type  = db.Column(db.String(50), nullable=True)
    # e.g.: 'heat_exchanger', 'reactor', 'general', 'optimization'

    tokens_used   = db.Column(db.Integer, nullable=True)  # Groq token count
    response_time = db.Column(db.Float,   nullable=True)  # seconds

    # ── Rating (optional user feedback) ─────────────────────
    rating        = db.Column(db.Integer, nullable=True)  # 1–5

    # ── Timestamp ────────────────────────────────────────────
    created_at    = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            'id':            self.id,
            'user_message':  self.user_message,
            'ai_response':   self.ai_response,
            'context_type':  self.context_type,
            'created_at':    self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        snippet = self.user_message[:40] if self.user_message else ''
        return f'<ChatHistory user={self.user_id} "{snippet}...">'
