from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    attachments = db.relationship(
        'NoteAttachment',
        backref='note',
        cascade='all, delete-orphan',
        lazy=True,
    )
    
    def __repr__(self):
        return f'<Note {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'attachments': [attachment.to_dict() for attachment in self.attachments],
        }


class NoteAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)
    content_type = db.Column(db.String(128), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.original_name,
            'content_type': self.content_type,
            'size': self.size,
            'url': f'/api/attachments/{self.id}',
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

