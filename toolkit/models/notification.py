import datetime
from toolkit import db


class Notification(db.Model):
    """Notification model."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text)
    notification_type = db.Column(db.String(30), default='info')  # info, success, warning, error, system
    icon = db.Column(db.String(64))
    link = db.Column(db.String(256))
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Indexes for faster querying
    __table_args__ = (
        db.Index('idx_notifications_user_created', 'user_id', 'created_at'),
        db.Index('idx_notifications_is_read', 'is_read'),
    )

    def __repr__(self):
        return f'<Notification {self.id} for user {self.user_id}>'

    def to_dict(self):
        """Convert notification to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'notification_type': self.notification_type,
            'icon': self.icon,
            'link': self.link,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.datetime.utcnow()
            db.session.add(self)