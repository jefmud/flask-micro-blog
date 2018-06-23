from flask import g
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField,
                     BooleanField, TextAreaField, HiddenField, SelectField)
from flask_ckeditor import CKEditorField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from werkzeug.security import generate_password_hash
from utils import slugify
import os

# if programmer wants to limit choices, you could cut this list back
# uses the CDN from bootswatch.com
bootswatch_themes = ['cerulean', 'cosmo', 'cyborg', 'darkly', 'flatly', 'journal',
                     'litera', 'lumen', 'lux', 'materia', 'minty', 'pulse', 'sandstone', 'simplex',
                     'sketchy', 'slate', 'solar', 'spacelab', 'superhero', 'united', 'yeti']

# create the bootswatch theme choice list
theme_choices = []
for theme in bootswatch_themes:
    theme_choices.append((theme,theme))

# get extended themes (directory name of non-bootswatch/default)
# a tad awkward, perhaps should be stored in the database at startup?
theme_extended_choices = theme_choices[:]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for theme in os.listdir(os.path.join(BASE_DIR, 'templates/themes')):
    # stored as tuples for the WTForm SelectField
    theme_extended_choices.append((theme,theme))


class BaseForm(FlaskForm):
    """All forms inherit from BaseForm"""
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
    # check hashing type, rehash if not hashed
    if not ('pbkdf2:sha256' in field.data):
        field.data = generate_password_hash(field.data)
        
def autoslug(form, field):
    """if slug is empty, autoslug it"""
    if field.data == "":
        field.data = slugify(form.title.data)
        
class FileForm(BaseForm):
    title = StringField('Filename/Title')
    filepath = StringField('File Path')
    owner = StringField()
    submit = SubmitField('Save')
    
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
    """Base Page Information Form, content is added via PageForm (below)"""
    owner = StringField('Owner')
    title = StringField('Title', validators=[DataRequired()])
    slug = StringField('Custom Slug (optional)',
                       description='if you omit this field, the slug is auto-generated from the title',
                       validators=[autoslug])
    is_published = BooleanField('is published')
    theme = SelectField('Theme selector', choices=theme_extended_choices)
    # maybe add markdown later--
    # markdown would be a good choice for unprivileged editors
    # but... we can put a safety filter on HTML as it goes into the database, it could strip script tags
    # is_markdown = BooleanField('use markdown format')
    
class PageForm(PageInfoForm):
    """Inherits PageInfoForm, non-HTML"""
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Save Page')
    
class HTMLPageForm(PageForm):
    """CKEditor content overrides content with the CKEditor HTML"""
    content = CKEditorField('Content', validators=[DataRequired()])
    
class AdminPageForm(PageForm):
    """Administor pages, hide the submit button in Flask-Admin interface"""
    submit = HiddenField() # hide the button
    
class AdminSiteMeta(BaseForm):
    """Site Meta form"""
    brand = StringField('Site Brand', validators=[DataRequired()])
    theme = SelectField('Bootswatch Theme CDN', choices=theme_choices)
    navbackground = BooleanField('Navbar Background dark theme')
    # logo, description not implemented yet
    description = CKEditorField('Description')
    # logo will be an image URL or Local File (use custom validator?)
    logo = StringField()
    submit = SubmitField('Save Meta')