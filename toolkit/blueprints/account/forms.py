from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from toolkit.models.user import User


class LoginForm(FlaskForm):
    """Login form."""
    username = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """Registration form."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64,
               message='Username must be between 3 and 64 characters')])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """Validate username uniqueness."""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already exists. Please use a different username.')

    def validate_email(self, email):
        """Validate email uniqueness."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different email address.')


class ForgotPasswordForm(FlaskForm):
    """Forgot password form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')


class ResetPasswordForm(FlaskForm):
    """Reset password form."""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')])
    password2 = PasswordField('Repeat New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Change Password')


class ChangePasswordForm(FlaskForm):
    """Change password form for logged-in users."""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')])
    new_password2 = PasswordField('Repeat New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')


class ProfileForm(FlaskForm):
    """Profile editing form."""
    display_name = StringField('Display Name', validators=[
        Length(max=64, message='Display name must be less than 64 characters')])
    bio = TextAreaField('Bio', validators=[
        Length(max=500, message='Bio must be less than 500 characters')])
    avatar_url = StringField('Avatar URL', validators=[
        Length(max=256, message='Avatar URL must be less than 256 characters')])
    submit = SubmitField('Update Profile')


class EmailForm(FlaskForm):
    """Email change form."""
    email = StringField('New Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Change Email')

    def validate_email(self, email):
        """Validate email uniqueness."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different email address.')


class OAuthBindForm(FlaskForm):
    """OAuth binding form."""
    provider = StringField('Provider', validators=[DataRequired()])
    submit = SubmitField('Bind Account')


class OAuthUnbindForm(FlaskForm):
    """OAuth unbinding form."""
    provider = StringField('Provider', validators=[DataRequired()])
    submit = SubmitField('Unbind Account')