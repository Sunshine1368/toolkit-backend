import datetime
from toolkit import db


class Message(db.Model):
    """Message model for chat."""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, image, file, system
    media_url = db.Column(db.String(256))
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Indexes for faster querying
    __table_args__ = (
        db.Index('idx_messages_sender_recipient', 'sender_id', 'recipient_id'),
        db.Index('idx_messages_created_at', 'created_at'),
    )

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id} to {self.recipient_id}>'

    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'content': self.content,
            'message_type': self.message_type,
            'media_url': self.media_url,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def mark_as_read(self):
        """Mark message as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.datetime.utcnow()
            db.session.add(self)