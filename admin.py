# admin.py
# modify this for additional administrative views

from flask import abort, g, render_template, redirect, session

# adding flask_admin
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.pymongo import ModelView

import os

import forms

# flask-admin setup
class MyAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        if g.is_admin:
            return render_template('admin.html')
        abort(403)
    
class UserView(ModelView):
    def is_accessible(self):
        return g.is_admin
    
    # This view is used by admin, see initialize
    column_list = ('username', 'email', 'is_admin', 'is_active', 'display_name', 'avatar', 'bio', 'password' )
    column_sortable_list = ('username', 'email')
    
    form = forms.AdminUserForm
    
    page_size = 20
    can_set_page_size = True
    
class PageView(ModelView):
    def is_accessible(self):
        return g.is_admin
    
    column_list = ('owner', 'slug', 'title', 'is_published')
    column_sortable_list = ('owner', 'slug', 'title','is_published')
    
    form = forms.AdminPageForm
    page_size = 20
    can_set_page_size = True
    
class DeletedView(ModelView):
    def is_accessible(self):
        return g.is_admin
    
    column_list = ('owner', 'slug', 'title')
    column_sortable_list = ('owner','slug','title')
    
    form = forms.AdminPageForm
    page_size = 20
    can_set_page_size = True
    
class FileView(ModelView):
    def is_accessible(self):
        return g.is_admin
    
    column_list = ('owner','title','filepath')
    column_sortable_list = ('owner','title','filepath')
    
    form = forms.FileForm
    page_size = 20
    can_set_page_size = True
    
class SiteMetaView(BaseView):
    def is_accessible(self):
        return g.is_admin
    
    @expose('/', methods=['POST','GET'])
    def index(self):
        # get the FIRST meta object
        meta = g.db.meta.find_one({})
        # get the WTForm from forms.py
        form = forms.AdminSiteMeta()
        
        if form.validate_on_submit():
            # theme comes from a select list
            meta['theme'] = form.theme.data # select list of bootswatch themes
            meta['brand'] = form.brand.data # string field, input required
            meta['navbackground'] = form.navbackground.data # boolean field
            # description and logo are currently not implemented
            meta['description'] = form.description.data # ckeditor
            meta['logo'] = form.logo.data # should be a URL or Local file
            # save the metadata object
            g.db.meta.update_one({'_id': meta['_id']}, meta)
        else:
            # supply some defaults to the form if not present in meta-object
            form.theme.data = meta.get('theme', 'materia')
            form.brand.data = meta.get('brand', 'FlaskMicroBlog')
            form.navbackground.data = meta.get('navbackground', False)
            
        return self.render('admin/blog_meta.html',form=form)
    
class NotificationsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/notify.html')

#class FileView(BaseView):
    #@expose('/')
    #def index(self):
        #files = g.db.files.find()
        #return self.render('admin/files.html',files=files)
    
def initialize(app, db):
    #admin = Admin(app, name='FlaskMicroBlog', template_mode='bootstrap3', index_view=MyAdminView())
    admin = Admin(app, name='FlaskMicroBlog', template_mode='bootstrap3')
    admin.add_view(UserView(db.users,'Users'))
    admin.add_view(PageView(db.pages,'Pages'))
    admin.add_view(DeletedView(db.deleted,'Deleted'))
    admin.add_view(FileView(db.files,'Files'))
    admin.add_view(SiteMetaView(name='SiteMeta', endpoint='sitemeta'))
    admin.add_view(NotificationsView(name='Notifications', endpoint='notify'))
   

    return admin
