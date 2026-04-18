import datetime
from toolkit import db


class Contact(db.Model):
    """Contact relationship model."""
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    nickname = db.Column(db.String(64))
    notes = db.Column(db.Text)
    is_favorite = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Unique constraint to prevent duplicate contacts
    __table_args__ = (
        db.UniqueConstraint('user_id', 'contact_id', name='unique_contact'),
    )

    def __repr__(self):
        return f'<Contact {self.user_id} -> {self.contact_id}>'

    def to_dict(self):
        """Convert contact to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'contact_id': self.contact_id,
            'nickname': self.nickname,
            'notes': self.notes,
            'is_favorite': self.is_favorite,
            'is_blocked': self.is_blocked,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }