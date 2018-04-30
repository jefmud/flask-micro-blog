from flask import g
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, HiddenField
from flask_ckeditor import CKEditorField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from werkzeug.security import generate_password_hash
from utils import slugify

class BaseForm(FlaskForm):
    # this base form allows form inheritance order to affect screen order
    # it works, but I think it is "programming by side-effect" sleight of hand
    def __iter__(self):
        token = self.csrf_token
        yield token

        field_names = {token.name}
        for cls in self.__class__.__bases__:
            for field in cls():
                field_name = field.name
                if field_name not in field_names:
                    field_names.add(field_name)
                    yield self[field_name]

        for field_name in self._fields:
            if field_name not in field_names:
                yield self[field_name]
                
def username_exists(form, field):
    """username_exists validator"""
    # make sure username is UNIQUE
    u = g.db.users.find_one({'username':form.username.data})
    if u:
        # user already exists, raise a validation error
        raise ValidationError("Username already exists!")
    
def autohash(form, field):
    """hash password if necessary"""
    if not ('pbkdf2:sha256' in field.data):
        field.data = generate_password_hash(field.data)
        
def autoslug(form, field):
    """if slug is empty, autoslug it"""
    if field.data == "":
        field.data = slugify(form.title.data)
    
class UserExtrasForm(BaseForm):
    display_name = StringField('Display Name')
    email = StringField('Email (optional)')    
    bio = CKEditorField('User Bio (optional)')
    avatar = StringField('Avatar Photo (optional)', description='URL or local photo id')
    
class UsernamePasswordForm(BaseForm):
    """simple form of username/password and datarequired validation"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    
class UsernamePasswordFormValidate(BaseForm):
    username = StringField('Username', validators=[DataRequired(), username_exists])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5), EqualTo('password2', message='Password must match')])
    password2 = PasswordField('Confirm',)
    
class LoginForm(UsernamePasswordForm):
    submit = SubmitField('Login')

class RegisterForm(UsernamePasswordFormValidate, UserExtrasForm):
    submit = SubmitField('Register')

class AdminUsernamePasswordForm(UsernamePasswordForm):
    """override of UsernamePasswordField
    1) allows us to SEE the HASHED password - normal PasswordField would not populate
    2) password is "autohashed" if it is not hashed/salted
    """
    password = StringField('Password', validators=[DataRequired(), autohash])
    
class AdminUserForm(AdminUsernamePasswordForm, UserExtrasForm):
    # combine UsernamePassword and UserExtras Form -- this also enforces order.
    is_admin = BooleanField('is admin')
    is_active = BooleanField('is active')

class PageInfoForm(BaseForm):
    owner = StringField('Owner')
    title = StringField('Title', validators=[DataRequired()])
    slug = StringField('Custom Slug (optional)',
                       description='if you omit this field, the slug is auto-generated from the title',
                       validators=[autoslug])
    is_published = BooleanField('is published')
    is_markdown = BooleanField('use markdown format')
    
class PageForm(PageInfoForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Save Page')
    
class HTMLPageForm(PageForm):
    content = CKEditorField('Content', validators=[DataRequired()])
    
class AdminPageForm(PageForm):
    submit = HiddenField() # hide the button