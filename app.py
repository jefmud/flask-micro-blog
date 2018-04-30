from flask import abort, flash, Flask, g, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor

from tinymongo import TinyMongoClient, Query, where

from utils import slugify, form2object, object2form
from markdown2 import markdown

from forms import LoginForm, HTMLPageForm, PageForm, RegisterForm
import os
import admin


app = Flask(__name__)
app.secret_key = 'youCanDoBetterThanThis'
DB = TinyMongoClient().blog
Bootstrap(app)
ckeditor = CKEditor(app)
admin.initialize(app, DB)

HOST = '0.0.0.0'
PORT = 5000
DEBUG = False

### FILE UPLOADS PARAMETERS
# UPLOAD FOLDER will have to change based on your own needs/deployment scenario
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, './uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


def create_user(username, password, email='', is_admin=False, is_active=True, bio="", avatar=""):
    """create a user, hash the password"""
    # make sure username is UNIQUE
    u = DB.users.find_one({'username':username})
    if u:
        # user already exists, return None
        return None
    hashedpw = generate_password_hash(password)
    u = DB.users.insert_one({'username':username, 'password':hashedpw, 'is_admin':is_admin,
                      'email':email, 'is_active':is_active, 'bio':bio, 'avatar':avatar})
    return u
    
    
def initialize():
    # this is called before the app starts
    # we're using a separte function because it has hashing and checking
    u  = create_user(username='admin', password='admin', is_admin=True)
    if u:
        print('User created')
    # These are the default HOME and ABOUT pages-- can be easily changed later.
    p = DB.pages.find_one({'slug':'home'})
    if p is None:
        DB.pages.insert_one({'slug':'home', 'title':'Home', 'owner':'admin',
        'content':'<b>Welcome, please change me.</b>  I am the <i>default</i> Home page!', 
        'is_markdown':False, 'owner':'admin', 'is_published': True})
        print("default HOME page created")
    p = DB.pages.find_one({'slug':'about'})
    if p is None:
        DB.pages.insert_one({'slug':'about', 'title':'About', 'owner':'admin',
        'content':'<b>Welcome</b>, please change me.  I am the <i>default</i> boilerplate About page.',
        'is_markdown':False, 'owner':'admin', 'is_published': True})
        print("default ABOUT page created")
    

@app.before_request
def before_request():
    g.db = DB
    g.is_authenticated = session.get('is_authenticated')
    g.is_admin = session.get('is_admin')
    g.username = session.get('username')
    # the brand will come from a "meta" object
    g.brand = "FlaskMicroBlog"
    
@app.after_request
def after_request(response):
    return response

@app.route('/template')
def template():
    return render_template('template.html')
    
@app.route('/login', methods=['GET','POST'])
def login():
    if g.is_authenticated:
        flash('Please logout first', category='warning')
        return redirect(url_for('site'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # see if user exists
        user = g.db.users.find_one({'username':form.username.data})
        if user:
            if check_password_hash(user.get('password'), form.password.data):
                # inject session data
                session['username'] = form.username.data
                session['is_authenticated'] = True
                if user.get('is_admin'):
                    session['is_admin'] = True
                
                msg = "Welcome {}!".format(form.username.data)
                flash(msg, category="success")
                return redirect(url_for('site'))
            
        flash("Incorrect username or password",category="danger")
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        flash("the data validated", category="success")
    return render_template('generic_form_ckedit.html', form=form)

def allowed_file(filename):
    """return True if filename is allowed for upload, False if not allowed"""
    return '.' in filename and \
         filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<path:path>')
def file_uploads(path):
    """serve up a file in our uploads"""
    print("access path={}".format(path))
    return send_from_directory(app.config['UPLOAD_FOLDER'], path)

@app.route('/admin')
def admin():
    if not g.is_admin:
        abort(403)
    return render_template('admin.html')

@app.route('/page/create', methods=['GET','POST'])
@app.route('/page/edit/<id>', methods=['GET','POST'])
def page_edit(id=None):
    """edit or create a page"""
    if not g.is_authenticated:
        flash('Please login first', category='warning')
        return redirect(url_for('login'))
    
    page = g.db.pages.find_one({'_id':id})
    if id:
        if page is None:
            abort(404)
    else:
        # create a NEW page here
        page = {}
    
    if page.get('is_markup'):
        page_template = 'generic_form.html'
        form = PageForm()
    else:
        page_template = 'generic_form_ckedit.html'
        form = HTMLPageForm()
    
    if form.validate_on_submit():
        page = form2object(form, page)
        if form.slug.data == '':
            page['slug'] = slugify(page['title'])
        if id:
            g.db.pages.update_one({'_id':id}, page)
        else:
            g.db.pages.insert_one(page)
            
        flash('Page saved.', category="info")
        return redirect(url_for('site', path=page.get('slug')))
    
    if request.method == 'GET':
        # get the data from the page-object into the form
        form = object2form(page, form)
    
    return render_template(page_template, form=form, id=id, title="Edit page")

@app.route('/page/delete/<id>')
def page_delete(id):
    if not g.is_admin:
        abort(403)
    pquery = {'_id':id}
    page = g.db.pages.find_one(pquery)
    if page is None:
        abort(404)
        
    g.db.pages.delete_many(pquery)
    
    # make sure we can safely redirect to referrer-- if not, go to top-level of site
    if request.referrer == None or url_for('page_edit', id=id) in request.referrer:
        return redirect(url_for('site'))
    else:
        return redirect(request.referrer)
    
@app.route('/logout')
def logout():
    session.clear()
    flash("You are now logged out!",category="info")
    return redirect(url_for('site'))

# this is the general route "catchment"
@app.route("/")
@app.route("/<path:path>")
def site(path=None):
    """view for pages referenced via their slug (which can look like a path
    If you want to modify what happens when an empty path comes in
    See below, it is redirected to "index" view.  This can be changed via code below.
    """
    s = request.args.get('s')
    if s:
        return redirect( url_for('search', s=s) )
    
    if path is None:
        """modify here to change behavior of the home-index"""
        path = 'home'
    
    page = g.db.pages.find_one({'slug': path})
    if page is None:
        abort(404)
        
    if page.get('is_markdown'):
        page['content'] = markdown(page.get('content'))
      
    return render_template('page.html', page=page)   

  

if __name__ == '__main__':
    initialize()
    app.run(host=HOST, port=PORT, debug=DEBUG)