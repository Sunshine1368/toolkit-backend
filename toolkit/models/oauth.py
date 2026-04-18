import datetime
from toolkit import db


class OAuth(db.Model):
    """OAuth connection model for third-party authentication."""
    __tablename__ = 'oauth'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # github, google, etc.
    provider_user_id = db.Column(db.String(255), nullable=False)
    access_token = db.Column(db.String(512))
    refresh_token = db.Column(db.String(512))
    token_expires = db.Column(db.DateTime)
    profile_data = db.Column(db.JSON)  # Store provider-specific profile data
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('oauth_connections', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_user_id', name='unique_provider_user'),
        db.UniqueConstraint('user_id', 'provider', name='unique_user_provider'),
    )

    def __repr__(self):
        return f'<OAuth {self.provider}:{self.provider_user_id} for user {self.user_id}>'

    def to_dict(self):
        """Convert OAuth connection to dictionary."""
        return {
            'id': self.id,
            'provider': self.provider,
            'provider_user_id': self.provider_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def find_by_provider_user_id(cls, provider, provider_user_id):
        """Find OAuth connection by provider and provider user ID."""
        return cls.query.filter_by(
            provider=provider,
            provider_user_id=provider_user_id
        ).first()

    @classmethod
    def find_by_user_and_provider(cls, user_id, provider):
        """Find OAuth connection by user ID and provider."""
        return cls.query.filter_by(
            user_id=user_id,
            provider=provider
        ).first()

    @classmethod
    def create_or_update(cls, user_id, provider, provider_user_id, access_token=None,
                         refresh_token=None, token_expires=None, profile_data=None):
        """Create or update OAuth connection."""
        oauth = cls.find_by_user_and_provider(user_id, provider)
        if oauth:
            oauth.access_token = access_token
            oauth.refresh_token = refresh_token
            oauth.token_expires = token_expires
            oauth.profile_data = profile_data
            oauth.updated_at = datetime.datetime.utcnow()
        else:
            oauth = cls(
                user_id=user_id,
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires=token_expires,
                profile_data=profile_data
            )
            db.session.add(oauth)

        db.session.commit()
        return oauth