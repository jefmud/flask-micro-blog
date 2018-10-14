from flask import (abort, flash, Flask, g, redirect,
                   render_template, request, send_from_directory, session, url_for)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_dropzone import Dropzone
import datetime

from tinymongo import TinyMongoClient, Query, where

from utils import (slugify, form2object, object2form, login_required,
                   admin_required, strip_tags, password_generator)
from markdown2 import markdown

from forms import LoginForm, HTMLPageForm, PageForm, RegisterForm, FileForm, bootswatch_themes
import os, sys
import admin


app = Flask(__name__)
app.config.from_pyfile('app.cfg')
DB = TinyMongoClient().blog

Bootstrap(app)
ckeditor = CKEditor(app)
admin.initialize(app, DB)
dropzone = Dropzone()
dropzone.init_app(app)


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

def createsuperuser():
    """interactive CLI create user"""
    username = input("Enter the username: ")
    password = input("Enter the password: ")
    if create_user(username=username, password=password, is_admin=True, is_active=True) is None:
        print("Username already exists, choose a new one.")
    else:
        print("User successfully created.")

def initialize():
    """initialize the app"""
    # this is called before the app starts
    # we're using a separte function because it has hashing and checking
    admin='admin'
    password = password_generator()
    u  = create_user(username=admin,
                     password=password,
                     is_admin=True)
    if u:
        # replace with a randomization
        print('WRITE THIS DOWN!')
        print('Admin user created. username={} password={}'.format(admin, password))
        
    # These are the default HOME and ABOUT pages-- can be easily changed later.
    # will not overwrite existing home and about pages.
    p = DB.pages.find_one({'slug':'home'})
    if p is None:
        # create only if page IS NOT present
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
        
    m = DB.meta.find_one({})
    if m is None:
        DB.meta.insert_one({'brand':'FlaskMicroBlog', 'theme':'materia'})

@app.before_request
def before_request():
    g.db = DB
    g.is_authenticated = session.get('is_authenticated')
    g.is_admin = session.get('is_admin')
    g.username = session.get('username')
    # the brand will come from a "meta" object
    meta = g.db.meta.find_one({})
    g.theme = meta.get('theme','materia')
    g.brand = meta.get('brand')
    g.navbackground = meta.get('navbackground', False)

@app.after_request
def after_request(response):
    return response

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
                return redirect(url_for('site', next=request.url))

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
#@login_required
def file_uploads(path):
    """serve up a file in our uploads"""
    print("access path={}".format(path))
    return send_from_directory(app.config['UPLOAD_FOLDER'], path)

#@app.route('/admin')
#def admin():
    #if not g.is_admin:
        #abort(403)
    #return render_template('admin.html')

@app.route('/page/create', methods=['GET','POST'])
@app.route('/page/edit/<id>', methods=['GET','POST'])
@login_required
def page_edit(id=None):
    """edit or create a page"""

    page = g.db.pages.find_one({'_id':id})

    if id:
        if page is None:
            abort(404)
    else:
        # create a NEW page here
        page = {'owner':g.username}

    if page.get('owner') != g.username and not(g.is_admin):
        flash("You are not the page owner",category="danger")
        return redirect(url_for('site',path=page['slug']))    

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
@login_required
def page_delete(id):
    pquery = {'_id':id}
    page = g.db.pages.find_one(pquery)
    
    if page.get('owner') != g.username or g.is_admin:
        abort(403)
        
    if page is None:
        abort(404)

    g.db.pages.delete_many(pquery)
    g.db.deleted.insert(page)

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

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def file_upload():
    """File upload handling"""
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            subfolder = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m/")
            pathname = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)

            # handle name collision if needed
            # filename will add integers at beginning of filename in dotted fashion
            # hello.jpg => 1.hello.jpg => 2.hello.jpg => ...
            # until it finds an unused name
            i=1
            while os.path.isfile(pathname):
                parts = filename.split('.')
                parts.insert(0,str(i))
                filename = '.'.join(parts)
                i += 1
                if i > 100:
                    # probably under attack, so just fail
                    raise ValueError("too many filename collisions, administrator should check this out")

                pathname = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)

            try:
                # ensure directory where we are storing exists, and create it
                directory = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                # finally, save the file AND create its resource object in database
                file.save(pathname)
                local_filepath = os.path.join(subfolder, filename)
                #file_object = File.create(title=filename, filepath=local_filepath, owner=session['user_id'])
                file_object = {'title': filename, 'filepath': local_filepath, 'owner': g.username}
                g.db.files.insert(file_object)
                flash("File upload success")
                return redirect(url_for('file_edit', id=file_object['_id']))
            except Exception as e:
                print(e)
                flash("Something went wrong here-- please let administrator know", category="danger")
                raise ValueError("Something went wrong with file upload.")

    # TODO, replace with fancier upload drag+drop
    # session['no_csrf'] = True
    return render_template('admin/upload.html')


@app.route('/file/edit/<id>', methods=['GET','POST'])
@login_required
def file_edit(id):
    fileobj = g.db.files.find_one({'_id':id})
    
    if fileobj is None:
        abort(404)
        
    if fileobj.get('owner') != g.username or not(g.is_admin):
        # abort if owner doesn't match current user or current is not admin
        abort(403)
        
    form = FileForm()
    
    if form.validate_on_submit():
        fileobj = form2object(form, fileobj)
        flash('not implemented', category="warning")
    
    if request.method == 'GET':
        # get the data from the page-object into the form
        form = object2form(fileobj, form)
        
    return render_template('generic_form.html', form=form, title='Edit File')

# this is the search view
@app.route('/search')
def search():
    search_term = request.args.get('s')
    pages = list(g.db.pages.find())
    found = []
    for page in pages:
        if search_term.lower() in page.get('content').lower():
            found.append(page)
            
    return render_template('search.html', search_term=search_term, pages=found)

def find_shortcodes(content):
    """find and return shortcodes in the content"""
    shortcode_tag = app.config['SHORTCODE_TAG']
    shortcode_endtag = app.config['SHORTCODE_ENDTAG']
    shortcodes = []
    start_mark = 0
    while True:
        start_mark = content.find(shortcode_tag, start_mark)
        if start_mark < 0:
            break
        end_mark = content.find(shortcode_endtag, start_mark) + len(shortcode_endtag)
        shortcodes.append(content[start_mark:end_mark])
        start_mark = end_mark + 1
    return shortcodes

def page_mod_shortcodes(page, shortcodes):
    """takes in a page and alters using shortcodes, returns new page"""
    # theory, as shortcodes are processed, these turn into additional key value pairs on the page object
    # [[template sidebar-left.html]] would add page['template'] = 'sidebar-left.html'
    # if the first content keyword is "page" it fetches the page content referenced
    
    shortcode_tag = app.config['SHORTCODE_TAG']
    shortcode_endtag = app.config['SHORTCODE_ENDTAG']
    
    for shortcode in shortcodes:
        # remove tag markers and split on whitespace
        scs = shortcode
        scs = scs.replace(shortcode_tag,'')
        scs = scs.replace(shortcode_endtag,'')
        sclist = scs.split()
        if len(sclist) > 1:
            if sclist[0].lower() == "page":
                key = strip_tags(sclist[1].lower())
                slug = strip_tags(sclist[2].strip())
                cpage = g.db.pages.find_one({'slug':slug})
                page[key] = cpage['content']
            else:
                key = strip_tags(sclist[0]).strip() # have to strip_tags because of multiline shortcode
                value = scs[scs.find(key)+len(key):].strip() # exclude just the tag from the content
                page[key] = value
    
    # ensure that a default page-template is set (if it was not set in the shortcodes)
    page['template'] = page.get('template','page.html')
    page['theme'] = page.get('theme','default')
    
    if page['theme'] in bootswatch_themes:
        # bootswatch_themes are default theme set
        # slight weakness in design that we are dependent on SiteMeta navbackground setting
        g.theme = page['theme']
        page['theme'] == 'default'
        
    theme_path = os.path.join(BASE_DIR, 'templates', app.config['THEME_DIR'], page['theme'])
    
    if not os.path.exists(theme_path) or page['theme']=='':
        # in case user selected a non-existent theme
        page['theme'] = 'default'
    
    # note add some error trapping here,
    # if somehow there is a non-existent template, we should flash error and put them on default
    # page template.
    page['template'] = "{}/{}/{}".format(app.config['THEME_DIR'], page['theme'], page['template'])
    
    # remove shortcodes from display content
    for shortcode in shortcodes:
        page['content'] = page['content'].replace(shortcode,'')
        
    return page
        
# this is the general SITE route "catchment" for page view
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
        
    # get shortcodes
    shortcodes = find_shortcodes(page.get('content'))
    
    # modify page object with shortcode content directives, return new object
    page = page_mod_shortcodes(page, shortcodes)
    try:
        return render_template(page['template'], page=page)
    except:
        flash("Template <{}> not found".format(page['template']), category="danger")
        return render_template('themes/default/page.html', page=page)



if __name__ == '__main__':
    if DB.pages.find_one({'slug':'home'}) is None:
        print("please use '--initialize' command line argument for first use")
        
    if '--initialize' in sys.argv:
        initialize()
        sys.exit(0)
        
    if '--createsuperuser' in sys.argv:
        createsuperuser()
        sys.exit(0)
    
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])