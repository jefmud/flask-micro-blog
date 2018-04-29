# admin.py
# modify this for additional administrative views

from flask import abort, g, render_template, redirect, session

# adding flask_admin
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.pymongo import ModelView

import forms

# flask-admin setup
class MyAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        if g.is_admin:
            return render_template('admin.html')
        abort(403)
    
class UserView(ModelView):
    # This view is used by admin, see initialize
    column_list = ('username', 'email', 'is_admin', 'is_active', 'display_name', 'avatar', 'bio', 'password' )
    column_sortable_list = ('username', 'email')
    
    form = forms.AdminUserForm
    
    page_size = 20
    can_set_page_size = True
    
class PageView(ModelView):
    column_list = ('owner', 'slug', 'title', 'is_published')
    column_sortable_list = ('owner', 'slug', 'title','is_published')
    
    form = forms.AdminPageForm
    page_size = 20
    can_set_page_size = True
        
def initialize(app, db):
    #admin = Admin(app, name='FlaskMicroBlog', template_mode='bootstrap3', index_view=MyAdminView())
    admin = Admin(app, name='FlaskMicroBlog', template_mode='bootstrap3')
    admin.add_view(UserView(db.users,'Users'))
    admin.add_view(PageView(db.pages,'Pages'))
   

    return admin
