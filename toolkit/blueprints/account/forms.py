from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_babel import lazy_gettext as _l
from toolkit.models.user import User


class LoginForm(FlaskForm):
    """Login form."""
    username = StringField(_l('Username or Email'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    """Registration form."""
    username = StringField(_l('Username'), validators=[
        DataRequired(),
        Length(min=3, max=64,
               message=_l('Username must be between 3 and 64 characters'))])
    email = StringField(_l('Email'), validators=[
        DataRequired(),
        Email(),
        Length(max=120)])
    password = PasswordField(_l('Password'), validators=[
        DataRequired(),
        Length(min=8, message=_l('Password must be at least 8 characters'))])
    password2 = PasswordField(_l('Repeat Password'), validators=[
        DataRequired(),
        EqualTo('password', message=_l('Passwords must match'))])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        """Validate username uniqueness."""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_l('Username already exists. Please use a different username.'))

    def validate_email(self, email):
        """Validate email uniqueness."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_l('Email already registered. Please use a different email address.'))


class ForgotPasswordForm(FlaskForm):
    """Forgot password form."""
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Reset Password'))


class ResetPasswordForm(FlaskForm):
    """Reset password form."""
    password = PasswordField(_l('New Password'), validators=[
        DataRequired(),
        Length(min=8, message=_l('Password must be at least 8 characters'))])
    password2 = PasswordField(_l('Repeat New Password'), validators=[
        DataRequired(),
        EqualTo('password', message=_l('Passwords must match'))])
    submit = SubmitField(_l('Change Password'))


class ChangePasswordForm(FlaskForm):
    """Change password form for logged-in users."""
    current_password = PasswordField(_l('Current Password'), validators=[DataRequired()])
    new_password = PasswordField(_l('New Password'), validators=[
        DataRequired(),
        Length(min=8, message=_l('Password must be at least 8 characters'))])
    new_password2 = PasswordField(_l('Repeat New Password'), validators=[
        DataRequired(),
        EqualTo('new_password', message=_l('Passwords must match'))])
    submit = SubmitField(_l('Change Password'))


class ProfileForm(FlaskForm):
    """Profile editing form."""
    display_name = StringField(_l('Display Name'), validators=[
        Length(max=64, message=_l('Display name must be less than 64 characters'))])
    bio = TextAreaField(_l('Bio'), validators=[
        Length(max=500, message=_l('Bio must be less than 500 characters'))])
    avatar_url = StringField(_l('Avatar URL'), validators=[
        Length(max=256, message=_l('Avatar URL must be less than 256 characters'))])
    submit = SubmitField(_l('Update Profile'))


class EmailForm(FlaskForm):
    """Email change form."""
    email = StringField(_l('New Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Change Email'))

    def validate_email(self, email):
        """Validate email uniqueness."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_l('Email already registered. Please use a different email address.'))


class OAuthBindForm(FlaskForm):
    """OAuth binding form."""
    provider = StringField(_l('Provider'), validators=[DataRequired()])
    submit = SubmitField(_l('Bind Account'))


class OAuthUnbindForm(FlaskForm):
    """OAuth unbinding form."""
    provider = StringField(_l('Provider'), validators=[DataRequired()])
    submit = SubmitField(_l('Unbind Account'))