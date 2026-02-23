import uuid
from datetime import datetime
from ..extensions import db

class CV(db.Model):
    __tablename__ = "cvs"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID(as_uuid=True), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    template_name = db.Column(db.String(100), nullable=False)
    cv_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
